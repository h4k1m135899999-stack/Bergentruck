# objects.py

import cv2
import numpy as np


class ObjectDetector:


    def __init__(self, area_destino_min_px=1500):
        self.area_destino_min_px = area_destino_min_px

        # ==========================
        # HSV DAS CORES
        # Ajustar conforme arena
        # ==========================


        # verde

        self.green_low = np.array(
            [35, 80, 40]
        )

        self.green_high = np.array(
            [85, 255, 255]
        )


        # vermelho
        # vermelho precisa de duas faixas HSV

        self.red_low1 = np.array(
            [0,100,80]
        )

        self.red_high1 = np.array(
            [10,255,255]
        )


        self.red_low2 = np.array(
            [170,100,80]
        )

        self.red_high2 = np.array(
            [180,255,255]
        )


        # prata
        # baixa saturação + brilho alto

        self.silver_low = np.array(
            [0,0,120]
        )

        self.silver_high = np.array(
            [180,60,255]
        )


        # preto

        self.black_low = np.array(
            [0,0,0]
        )

        self.black_high = np.array(
            [180,255,60]
        )



    def detect(self,hsv):


        black = self.detect_black(hsv)

        green = self.detect_green(hsv, black["y"])

        green_area = self.detect_destination_area(
            cv2.inRange(hsv, self.green_low, self.green_high)
        )

        red = self.detect_red(hsv)

        red_mask = cv2.bitwise_or(
            cv2.inRange(hsv, self.red_low1, self.red_high1),
            cv2.inRange(hsv, self.red_low2, self.red_high2),
        )
        red_area = self.detect_destination_area(red_mask)

        silver = self.detect_silver(hsv)

        obstacle = self.detect_obstacle(
            hsv
        )


        return {


            # verde

            "green_left":
                green["left"],

            "green_right":
                green["right"],

            "green_count":
                green["count"],

            "green_area": green_area,

            "red_area": red_area,



            # fitas

            "red":
                red,

            "silver":
                silver["found"],

            "silver_line": silver,

            "black_exit":
                black["found"],

            "black_exit_line": black,



            # obstáculo

            "obstacle":
                obstacle["found"],

            "obstacle_info": obstacle

        }



    # =====================================================
    # VERDE
    # =====================================================


    def detect_green(self, hsv, black_line_y):


        mask=cv2.inRange(
            hsv,
            self.green_low,
            self.green_high
        )


        mask=self.clean(mask)



        contours,_=cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )


        h,w=mask.shape

        center=w//2



        left=False
        right=False



        for c in contours:


            area=cv2.contourArea(c)


            if area < 100:
                continue



            M=cv2.moments(c)


            if M["m00"]==0:
                continue


            x=int(
                M["m10"]/
                M["m00"]
            )

            y = int(M["m01"] / M["m00"])

            # No frame, valores maiores de y ficam mais perto do robô. Assim,
            # o verde só é uma curva se for encontrado antes da faixa preta.
            if black_line_y is None or y <= black_line_y:
                continue


            if x<center:

                left=True

            else:

                right=True



        return {

            "left":left,

            "right":right,

            "count":
                int(left)+int(right)

        }





    # =====================================================
    # VERMELHO
    # =====================================================


    def detect_red(self,hsv):


        m1=cv2.inRange(
            hsv,
            self.red_low1,
            self.red_high1
        )


        m2=cv2.inRange(
            hsv,
            self.red_low2,
            self.red_high2
        )


        mask=cv2.bitwise_or(
            m1,
            m2
        )


        return self.has_horizontal_tape(
            mask
        )





    # =====================================================
    # PRATA
    # =====================================================


    def detect_silver(self,hsv):


        mask=cv2.inRange(
            hsv,
            self.silver_low,
            self.silver_high
        )


        return self.detect_horizontal_tape(mask, width=200)





    # =====================================================
    # SAÍDA PRETA
    # =====================================================


    def detect_black(self,hsv):


        mask=cv2.inRange(
            hsv,
            self.black_low,
            self.black_high
        )


        return self.detect_horizontal_tape(mask, width=150)

    def detect_horizontal_tape(self, mask, width):
        """Retorna posição e inclinação da maior faixa horizontal visível."""
        h, w = mask.shape
        region_start = int(h * 0.55)
        region = mask[region_start:h, :]
        contours, _ = cv2.findContours(
            region,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        candidatos = [
            contour for contour in contours
            if cv2.boundingRect(contour)[2] >= width
        ]
        if not candidatos:
            return {"found": False, "y": None, "position": None, "angle": None}

        contour = max(candidatos, key=cv2.contourArea)
        x, y, tape_width, tape_height = cv2.boundingRect(contour)
        vx, vy, px, py = cv2.fitLine(contour, cv2.DIST_L2, 0, 0.01, 0.01)
        angle = float(np.arctan2(vy.item(), vx.item()))
        return {
            "found": True,
            "y": region_start + y + tape_height // 2,
            "position": (x + tape_width // 2, region_start + y + tape_height // 2),
            "angle": angle,
        }





    # =====================================================
    # OBSTÁCULO - NOVA IMPLEMENTAÇÃO
    # =====================================================

    def detect_obstacle(self, hsv):
        """Detecta bloqueio geométrico no corredor à frente, sem usar cor.
        Retorna dicionário com found, bbox, area, confidence, center_coverage, evidence.
        """
        bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Parâmetros ajustáveis (calibrar em campo)
        AREA_MIN_FRAC = 0.025          # fração da área total da imagem (bbox do grupo)
        WIDTH_MIN_FRAC = 0.15          # fração da largura
        HEIGHT_MIN_FRAC = 0.12         # fração da altura
        ROI_TOP_FRAC = 0.30            # região de interesse: daqui até o fundo
        CORREDOR_L_FRAC = 0.20
        CORREDOR_R_FRAC = 0.80
        WEIGHT_AREA = 0.35
        WEIGHT_CORRIDOR = 0.30
        WEIGHT_NEAR = 0.25
        WEIGHT_CENTRAL = 0.10
        SCORE_THRESHOLD = 0.50
        CORRIDOR_COVERAGE_THRESHOLD = 0.25

        # Parâmetros para agrupamento de contornos
        GROUP_GAP_FRAC = 0.03          # distância máxima (fração da menor dimensão) entre retângulos para unir
        MIN_CONTOUR_AREA = 10          # descarta ruído muito pequeno (em pixels)

        top = int(h * ROI_TOP_FRAC)
        roi = gray[top:, :]

        # Suavização e detecção de bordas
        blurred = cv2.GaussianBlur(roi, (5, 5), 0)
        mediana = np.median(blurred)
        lower = max(15, int(mediana * 0.5))
        upper = min(255, int(mediana * 1.5))
        edges = cv2.Canny(blurred, lower, upper)
        kernel = np.ones((7, 7), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # --- 1. Extrair bounding boxes de todos os contornos (com y ajustado) ---
        rects = []  # (x, y, bw, bh, contour_area)
        for contour in contours:
            contour_area = cv2.contourArea(contour)
            if contour_area < MIN_CONTOUR_AREA:
                continue
            x, y_roi, bw, bh = cv2.boundingRect(contour)
            y = y_roi + top
            rects.append((x, y, bw, bh, contour_area))

        if not rects:
            return {"found": False, "bbox": None, "area": 0, "confidence": 0.0,
                    "center_coverage": 0.0, "evidence": {"reason": "no_contours"}}

        # --- 2. Agrupamento simples baseado em proximidade ---
        gap = int(min(w, h) * GROUP_GAP_FRAC)
        grupos = []  # cada grupo: [x, y, w, h, lista_de_areas_contorno]

        for (x, y, bw, bh, ca) in rects:
            adicionado = False
            for g in grupos:
                gx, gy, gw, gh, areas = g
                # Distância horizontal e vertical entre as bordas dos retângulos
                dist_h = max(0, max(x, gx) - min(x + bw, gx + gw))
                dist_v = max(0, max(y, gy) - min(y + bh, gy + gh))
                if dist_h <= gap and dist_v <= gap:
                    # Expande o bounding box do grupo
                    new_x = min(x, gx)
                    new_y = min(y, gy)
                    new_right = max(x + bw, gx + gw)
                    new_bottom = max(y + bh, gy + gh)
                    g[0] = new_x
                    g[1] = new_y
                    g[2] = new_right - new_x
                    g[3] = new_bottom - new_y
                    areas.append(ca)
                    adicionado = True
                    break
            if not adicionado:
                grupos.append([x, y, bw, bh, [ca]])

        # --- 3. Avaliar cada grupo como candidato a obstáculo ---
        corredor_l = int(w * CORREDOR_L_FRAC)
        corredor_r = int(w * CORREDOR_R_FRAC)
        area_min = w * h * AREA_MIN_FRAC
        width_min = w * WIDTH_MIN_FRAC
        height_min = h * HEIGHT_MIN_FRAC

        candidatos = []

        for g in grupos:
            x, y, gw, gh, areas = g
            bbox_area = gw * gh

            # Filtros de tamanho mínimo aplicados AO GRUPO
            if bbox_area < area_min or gw < width_min or gh < height_min:
                continue

            # Cobertura do corredor
            inter_w = max(0, min(x + gw, corredor_r) - max(x, corredor_l))
            cobre_corredor = inter_w / max(corredor_r - corredor_l, 1)

            # Proximidade (baseada na posição vertical do fundo do bounding box)
            bottom_y = y + gh
            near = min(1.0, max(0.0, (bottom_y - h * 0.55) / (h * 0.45)))

            # Centralidade horizontal
            center_x = x + gw / 2
            central = 1.0 - min(1.0, abs(center_x - w / 2) / (w * 0.5))

            # Área relativa (normalizada por 20% da imagem)
            area_rel = min(1.0, bbox_area / (w * h * 0.20))

            # Score combinado (mesmos pesos)
            score = (WEIGHT_AREA * area_rel +
                     WEIGHT_CORRIDOR * cobre_corredor +
                     WEIGHT_NEAR * near +
                     WEIGHT_CENTRAL * central)

            # Solidez como evidência secundária (bônus suave, nunca penaliza)
            total_contour_area = sum(areas)
            solidity = total_contour_area / bbox_area if bbox_area > 0 else 0.0
            if solidity > 0.7:
                score = min(1.0, score * 1.05)

            if score >= SCORE_THRESHOLD and cobre_corredor >= CORRIDOR_COVERAGE_THRESHOLD:
                candidatos.append((score, (x, y, gw, gh), bbox_area,
                                   cobre_corredor, near, central, solidity,
                                   len(areas), total_contour_area))

        if not candidatos:
            return {"found": False, "bbox": None, "area": 0, "confidence": 0.0,
                    "center_coverage": 0.0, "evidence": {"reason": "no_candidate_after_grouping"}}

        # --- 4. Escolher o melhor candidato ---
        melhor = max(candidatos, key=lambda item: item[0])
        score, bbox, bbox_area, corridor, near, central, solidity, group_size, total_contour_area = melhor

        return {
            "found": True,
            "bbox": bbox,
            "area": int(bbox_area),
            "confidence": float(score),
            "center_coverage": corridor,
            "evidence": {
                "bbox_area_rel": round(bbox_area / (w * h), 3),
                "contour_area_rel": round(total_contour_area / (w * h), 3),
                "corridor": round(corridor, 3),
                "near": round(near, 3),
                "central": round(central, 3),
                "solidity": round(solidity, 3),
                "group_size": group_size,
                "score": round(score, 3)
            }
        }
   
    def detect_destination_area(self, mask):
        """Retorna a maior área colorida que pode receber vítimas."""
        mask = self.clean(mask)
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:
            return None

        contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(contour) < self.area_destino_min_px:
            return None

        x, y, w, h = cv2.boundingRect(contour)
        return {
            "position": (x + w // 2, y + h // 2),
            "bottom_y": y + h,
        }





    # =====================================================
    # AUXILIARES
    # =====================================================


    def clean(self,mask):


        kernel=np.ones(
            (5,5),
            np.uint8
        )


        return cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            kernel
        )





    def has_horizontal_tape(
            self,
            mask,
            width=200):

        return self.horizontal_tape_y(mask, width) is not None


    def horizontal_tape_y(self, mask, width):


        h,w=mask.shape


        # olha só perto do robô

        region=mask[
            int(h*0.75):
            h,
            :
        ]

        contours, _ = cv2.findContours(
            region,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        for contour in contours:
            x, y, tape_width, tape_height = cv2.boundingRect(contour)
            if tape_width >= width:
                return int(h * 0.75) + y + tape_height // 2

        return None
