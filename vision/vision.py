# vision.py - VERSÃO OTIMIZADA PARA ALTO FPS
import cv2
import time
import setup
from .line import LineDetector
from .objects import ObjectDetector
from .victims import VictimDetector
from .debug import Debug
from .distance import EstimadorDistanciaCamera


class Vision:

    def __init__(self, camera_id=None, width=None, height=None):
        camera_id = setup.CAMERA_ID if camera_id is None else camera_id
        width = setup.FRAME_WIDTH if width is None else width
        height = setup.FRAME_HEIGHT if height is None else height

        # ===== MELHORIA 1: FORÇA BACKEND V4L2 =====
        # Tenta diferentes backends para evitar GStreamer
        backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
        self.cap = None
        
        for backend in backends:
            self.cap = cv2.VideoCapture(camera_id, backend)
            if self.cap.isOpened():
                print(f"✓ Câmera aberta com backend {backend}")
                break
        
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(camera_id)  # Última tentativa
            if not self.cap.isOpened():
                raise Exception("Camera não encontrada")

        # ===== MELHORIA 2: CONFIGURAÇÕES DE PERFORMANCE =====
        # Define resolução
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # BUFFER MENOR = MENOS ATRASO
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Força FPS (se a câmera suportar)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Desativa auto-exposição (mais rápido)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        
        # Verifica resolução real
        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Resolução real: {actual_w}x{actual_h}")
        
        # Flag para redimensionar se necessário
        self.resize_needed = (actual_w != width or actual_h != height)

        # ===== MELHORIA 3: CONTROLE DE FRAMES =====
        self.frame_count = 0
        self.process_every_n = 1  # 1 = processa todos, 2 = processa metade
        
        # ===== MELHORIA 4: FLAGS DE PROCESSAMENTO CONDICIONAL =====
        self.detect_objects = True   # Desative quando não precisar
        self.detect_victims = True   # Desative quando não precisar
        self.debug_mode = False      # Mantenha False para performance

        # Módulos
        self.line = LineDetector()
        self.objects = ObjectDetector(setup.AREA_DESTINO_MIN_PX)
        self.victims = VictimDetector()
        self.distance = EstimadorDistanciaCamera(
            setup.DIAMETRO_BOLA_MM,
            setup.DISTANCIA_FOCAL_PX,
        )
        self.debugger = Debug()

        # Estado
        self.frame = None
        self.hsv = None
        
        # Resultados linha
        self.line_found = False
        self.center_error = 0
        self.heading = 0
        self.curvature = 0
        self.skeleton = []
        self.line_mask = None
        self.line_confidence = 0.0

        # Objetos
        self.green_left = False
        self.green_right = False
        self.green_count = 0
        self.red = False
        self.silver = False
        self.silver_line = None
        self.black_exit = False
        self.black_exit_line = None
        self.obstacle = False
        self.obstacle_bbox = None
        self.obstacle_info = None
        self.green_area = None
        self.red_area = None

        # Vítimas
        self.victim_position = None
        self.victim_type = None
        self.victim_diameter_px = None
        self.victim_distance_mm = None
        self._victim_distance_filtered = None
        
        # ===== MELHORIA 5: CACHE DE PERFORMANCE =====
        self.last_frame_time = 0
        self.fps = 0

    def debug_frame(self):
        if not self.debug_mode:
            return self.frame
        return self.debugger.draw(self.frame, self)

    def update(self):
        # ===== MELHORIA 6: SKIP FRAMES =====
        self.frame_count += 1
        if self.frame_count % self.process_every_n != 0:
            # Ainda captura, mas não processa
            ok, _ = self.cap.read()
            return ok

        # Captura
        ok, frame = self.cap.read()
        if not ok:
            return False

        # Redimensiona se necessário
        if self.resize_needed:
            frame = cv2.resize(frame, (setup.FRAME_WIDTH, setup.FRAME_HEIGHT), 
                             interpolation=cv2.INTER_NEAREST)  # MAIS RÁPIDO que INTER_LINEAR

        self.frame = frame
        
        # ===== MELHORIA 7: HSV CONVERSION OPCIONAL =====
        # Só converte se precisar (linha precisa)
        self.hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # ===== MELHORIA 8: LINHA (SEMPRE NECESSÁRIA) =====
        line = self.line.detect(self.hsv)
        self.line_found = line["found"]
        self.center_error = line["error"]
        self.line_confidence = line.get("confidence", 0.0)
        self.heading = line["heading"]
        self.curvature = line["curvature"]
        self.skeleton = line["skeleton"]
        self.line_mask = line["mask"]

        # ===== MELHORIA 9: OBJETOS (CONDICIONAL) =====
        if self.detect_objects:
            obj = self.objects.detect(self.hsv)
            self.green_left = obj["green_left"]
            self.green_right = obj["green_right"]
            self.green_count = obj["green_count"]
            self.red = obj["red"]
            self.silver = obj["silver"]
            self.silver_line = obj["silver_line"]
            self.black_exit = obj["black_exit"]
            self.black_exit_line = obj.get("black_exit_line")
            self.obstacle = obj["obstacle"]
            self.obstacle_info = obj["obstacle_info"]
            self.obstacle_bbox = self.obstacle_info["bbox"] if self.obstacle_info else None
            self.green_area = obj["green_area"]
            self.red_area = obj["red_area"]
        else:
            # Mantém valores padrão (não processa)
            pass

        # ===== MELHORIA 10: VÍTIMAS (CONDICIONAL) =====
        if self.detect_victims:
            vic = self.victims.detect(self.hsv)
            self.victim_position = vic["position"]
            self.victim_type = vic["type"]
            self.victim_diameter_px = vic.get("diameter_px")
            
            distancia = self.distance.estimar_bola_mm(self.victim_diameter_px)
            if distancia is None:
                self._victim_distance_filtered = None
            elif self._victim_distance_filtered is None:
                self._victim_distance_filtered = distancia
            else:
                self._victim_distance_filtered = 0.65 * self._victim_distance_filtered + 0.35 * distancia
            self.victim_distance_mm = self._victim_distance_filtered
        else:
            self.victim_position = None
            self.victim_type = None
            self.victim_diameter_px = None
            self.victim_distance_mm = None

        # ===== MELHORIA 11: CÁLCULO DE FPS =====
        current_time = time.time()
        if self.last_frame_time > 0:
            self.fps = 1.0 / (current_time - self.last_frame_time)
        self.last_frame_time = current_time

        return True

    def set_processing_mode(self, mode):
        """
        Modos para economizar processamento:
        'line_only': Só linha (mais rápido)
        'line_objects': Linha + objetos
        'line_victims': Linha + vítimas
        'full': Tudo (mais lento)
        """
        if mode == 'line_only':
            self.detect_objects = False
            self.detect_victims = False
            self.process_every_n = 1
        elif mode == 'line_objects':
            self.detect_objects = True
            self.detect_victims = False
            self.process_every_n = 1
        elif mode == 'line_victims':
            self.detect_objects = False
            self.detect_victims = True
            self.process_every_n = 1
        elif mode == 'full':
            self.detect_objects = True
            self.detect_victims = True
            self.process_every_n = 1
        elif mode == 'turbo':
            self.detect_objects = False
            self.detect_victims = False
            self.process_every_n = 2  # Processa metade dos frames

    def release(self):
        if self.cap:
            self.cap.release()