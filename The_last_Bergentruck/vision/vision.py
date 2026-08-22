# vision.py

import cv2

from .line import LineDetector
from .objects import ObjectDetector
from .victims import VictimDetector
from .debug import Debug
from .distance import EstimadorDistanciaCamera
import setup


class Vision:

    def __init__(self, camera_id=None, width=None, height=None):

        camera_id = setup.CAMERA_ID if camera_id is None else camera_id
        width = setup.FRAME_WIDTH if width is None else width
        height = setup.FRAME_HEIGHT if height is None else height

        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if not self.cap.isOpened():
            raise Exception("Camera não encontrada")


        # módulos

        self.line = LineDetector()
        self.objects = ObjectDetector(setup.AREA_DESTINO_MIN_PX)
        self.victims = VictimDetector()
        self.distance = EstimadorDistanciaCamera(
            setup.DIAMETRO_BOLA_MM,
            setup.DISTANCIA_FOCAL_PX,
        )


        # debug

        self.debugger = Debug()


        # frame atual

        self.frame = None
        self.hsv = None


        # resultado linha

        self.line_found = False
        self.center_error = 0
        self.heading = 0
        self.curvature = 0
        self.skeleton = []
        self.line_mask = None
        self.line_confidence = 0.0


        # objetos

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
        self.obstacle_info = None   # <-- ADICIONADO
        self.green_area = None
        self.red_area = None


        # vítimas

        self.victim_position = None
        self.victim_type = None
        self.victim_diameter_px = None
        self.victim_distance_mm = None
        self._victim_distance_filtered = None


    def debug_frame(self):

        return self.debugger.draw(
            self.frame,
            self
        )


    def update(self):

        ok, frame = self.cap.read()

        if not ok:
            return False


        self.frame = frame


        self.hsv = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2HSV
        )


        # -----------------------
        # LINHA
        # -----------------------

        line = self.line.detect(
            self.hsv
        )


        self.line_found = line["found"]

        self.center_error = line["error"]
        self.line_confidence = line.get("confidence", 0.0)

        self.heading = line["heading"]

        self.curvature = line["curvature"]

        self.skeleton = line["skeleton"]
        self.line_mask = line["mask"]



        # -----------------------
        # OBJETOS
        # -----------------------

        obj = self.objects.detect(
            self.hsv
        )


        self.green_left = obj["green_left"]

        self.green_right = obj["green_right"]

        self.green_count = obj["green_count"]

        self.red = obj["red"]

        self.silver = obj["silver"]
        self.silver_line = obj["silver_line"]

        self.black_exit = obj["black_exit"]
        self.black_exit_line = obj["black_exit_line"] if "black_exit_line" in obj else None

        self.obstacle = obj["obstacle"]
        # CORREÇÃO: guarda o dicionário completo
        self.obstacle_info = obj["obstacle_info"]  # contém found, bbox, area, center_coverage, h_std, s_std
        # Atualiza bbox a partir do info
        self.obstacle_bbox = self.obstacle_info["bbox"] if self.obstacle_info else None

        self.green_area = obj["green_area"]
        self.red_area = obj["red_area"]



        # -----------------------
        # VÍTIMAS
        # -----------------------

        vic = self.victims.detect(
            self.hsv
        )


        self.victim_position = vic["position"]

        self.victim_type = vic["type"]

        self.victim_diameter_px = vic.get("diameter_px")

        distancia = self.distance.estimar_bola_mm(
            self.victim_diameter_px
        )
        # EMA reduz oscilações de tamanho entre frames sem atrasar excessivamente.
        if distancia is None:
            self._victim_distance_filtered = None
        elif self._victim_distance_filtered is None:
            self._victim_distance_filtered = distancia
        else:
            self._victim_distance_filtered = 0.65 * self._victim_distance_filtered + 0.35 * distancia
        self.victim_distance_mm = self._victim_distance_filtered



        return True


    def release(self):

        self.cap.release()
