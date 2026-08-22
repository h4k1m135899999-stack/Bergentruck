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
        """Detecta bloqueio geométrico no corredor à frente, sem usar cor."""
        bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        # ROI exclui teto/parede; obstáculo próximo deve ocupar a metade inferior.
        top = int(h * 0.30)
        roi = gray[top:, :]
        mediana = np.median(roi)
        edges = cv2.Canny(roi, max(15, int(mediana * .55)), min(255, int(mediana * 1.45)))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=2)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        corredor_l, corredor_r = int(w * .22), int(w * .78)
        candidatos = []
        for contour in contours:
            area = cv2.contourArea(contour)
            x, y_roi, bw, bh = cv2.boundingRect(contour)
            y = y_roi + top
            if area < w * h * .007 or bw < w * .12 or bh < h * .10:
                continue
            inter_w = max(0, min(x + bw, corredor_r) - max(x, corredor_l))
            cobre_corredor = inter_w / max(corredor_r - corredor_l, 1)
            proximo = min(1.0, max(0.0, (y + bh - h * .55) / (h * .45)))
            central = 1.0 - min(1.0, abs((x + bw / 2) - w / 2) / (w * .5))
            # Um bloco deve apresentar área, largura no corredor e proximidade.
            area_rel = min(1.0, area / (w * h * .20))
            score = .30 * area_rel + .30 * cobre_corredor + .25 * proximo + .15 * central
            if score >= .48 and cobre_corredor >= .25:
                candidatos.append((score, (x, y, bw, bh), area, cobre_corredor, proximo, central))
        if not candidatos:
            return {"found": False, "bbox": None, "area": 0, "confidence": 0.0,
                    "evidence": {"reason": "no_geometric_candidate"}}
        score, bbox, area, corridor, near, central = max(candidatos, key=lambda item: item[0])
        return {"found": True, "bbox": bbox, "area": area, "confidence": float(score),
                "center_coverage": corridor,
                "evidence": {"area": round(area / (w * h), 3), "corridor": round(corridor, 3),
                             "near": round(near, 3), "central": round(central, 3)}}


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
