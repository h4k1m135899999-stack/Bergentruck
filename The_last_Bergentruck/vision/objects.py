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
        """
        Detecta obstáculos baseado em bordas e homogeneidade de cor.
        
        Estratégia:
        1. Detecta bordas na imagem inteira usando Canny adaptativo
        2. Agrupa bordas em contornos
        3. Para cada contorno, verifica se a região interna tem cor homogênea
        4. Verifica se a região ocupa uma grande área central (>80%)
        5. Se sim, considera como obstáculo
        """
        h, w = hsv.shape[:2]
        
        # 1. Converter para BGR para processamento
        bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        
        # 2. Detecta bordas na imagem inteira com parâmetros adaptativos
        # Usamos um Canny com thresholds adaptativos baseados na mediana
        median = np.median(gray)
        lower = int(max(0, 0.66 * median))
        upper = int(min(255, 1.33 * median))
        
        edges = cv2.Canny(gray, lower, upper)
        
        # 3. Fecha pequenas lacunas nas bordas
        kernel = np.ones((5, 5), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # 4. Encontra contornos das regiões delimitadas por bordas
        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # 5. Define a região central (80% da área central da imagem)
        center_roi = (
            int(w * 0.1),   # 10% da esquerda
            int(h * 0.1),   # 10% do topo
            int(w * 0.8),   # 80% da largura
            int(h * 0.8)    # 80% da altura
        )
        cx, cy, cw, ch = center_roi
        center_area = cw * ch
        min_center_coverage = center_area * 0.7  # 80% da área central
        
        # A ordem dos contornos do OpenCV não é um critério de segurança.
        # Avaliamos todos e retornamos o candidato de maior confiança.
        candidatos = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Ignora contornos muito pequenos
            if area < 400:
                continue
            
            x, y, wc, hc = cv2.boundingRect(contour)
            
            # Verifica se o contorno ocupa uma grande parte da região central
            # Calcula a interseção do bounding box com a região central
            inter_x = max(x, cx)
            inter_y = max(y, cy)
            inter_w = min(x + wc, cx + cw) - inter_x
            inter_h = min(y + hc, cy + ch) - inter_y
            
            if inter_w > 0 and inter_h > 0:
                inter_area = inter_w * inter_h
                
                # Se a região cobre menos de 80% da área central, provavelmente não é obstáculo
                if inter_area < min_center_coverage:
                    continue
            else:
                continue
            
            # 7. Verifica homogeneidade da cor dentro do contorno
            # Cria uma máscara do contorno
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            
            # Calcula a variação de cor dentro do contorno
            masked_bgr = cv2.bitwise_and(bgr, bgr, mask=mask)
            
            # Calcula o desvio padrão da região (em HSV fica melhor)
            masked_hsv = cv2.bitwise_and(hsv, hsv, mask=mask)
            
            # Pega apenas os pixels válidos
            valid_pixels = masked_hsv[mask > 0]
            
            if len(valid_pixels) < 10:
                continue
            
            # Calcula a variação de cor (desvio padrão)
            # Usamos o canal H (matiz) e S (saturação) para verificar homogeneidade
            h_std = np.std(valid_pixels[:, 0])
            s_std = np.std(valid_pixels[:, 1])
            
            # Verifica a homogeneidade da região
            # Se a variação de matiz for baixa (< 30) e saturação baixa (< 40),
            # a região é considerada homogênea
            is_homogeneous = h_std < 30 and s_std < 40
            
            if not is_homogeneous:
                continue
            
            # 8. Verifica se o aspecto é razoável para um obstáculo (não é muito fino)
            aspect = wc / max(hc, 1)
            if aspect < 0.15 or aspect > 10:
                continue
            
            cobertura = inter_area / center_area
            score = (cobertura * 0.55 + min(area / center_area, 1.0) * 0.30
                     + (1 - (h_std / 30 + s_std / 40) / 2) * 0.15)
            candidatos.append((score, (x, y, wc, hc), area, cobertura, h_std, s_std))

        if candidatos:
            score, bbox, area, cobertura, h_std, s_std = max(candidatos, key=lambda item: item[0])
            return {"found": True, "bbox": bbox, "area": area,
                    "center_coverage": cobertura, "h_std": h_std, "s_std": s_std,
                    "confidence": float(score)}
        
        return {"found": False, "bbox": None, "area": 0, "center_coverage": 0}


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
