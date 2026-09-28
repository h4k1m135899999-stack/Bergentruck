# masks.py — vistas de máscara HSV / Canny iguais ao que os detectores usam.

import cv2
import numpy as np


class MaskViews:

    MODE_NAMES = {
        "o": "OVERLAY (tudo)",
        "l": "LINHA (preta)",
        "g": "VERDE",
        "r": "VERMELHO",
        "s": "PRATA (fita)",
        "b": "PRETO (saida)",
        "v": "VITIMAS",
        "k": "OBSTACULO (bordas)",
        "d": "DESTINOS (areas)",
        "n": "ORIGINAL",
    }

    def render(self, vision, mode: str):
        frame = vision.frame
        hsv = vision.hsv
        objects = vision.objects
        victims = vision.victims
        line = vision.line

        if mode == "l":
            mask = cv2.inRange(hsv, line.low, line.high)
            return self._gray_bgr(mask)

        if mode == "g":
            mask = cv2.inRange(hsv, objects.green_low, objects.green_high)
            return self._gray_bgr(mask)

        if mode == "r":
            m1 = cv2.inRange(hsv, objects.red_low1, objects.red_high1)
            m2 = cv2.inRange(hsv, objects.red_low2, objects.red_high2)
            return self._gray_bgr(cv2.bitwise_or(m1, m2))

        if mode == "s":
            mask = cv2.inRange(hsv, objects.silver_low, objects.silver_high)
            return self._gray_bgr(mask)

        if mode == "b":
            mask = cv2.inRange(hsv, objects.black_low, objects.black_high)
            return self._gray_bgr(mask)

        if mode == "v":
            show = frame.copy()
            ms = cv2.inRange(hsv, victims.silver_low, victims.silver_high)
            md = cv2.inRange(hsv, victims.dark_low, victims.dark_high)
            show[ms > 0] = (200, 200, 200)
            show[md > 0] = (40, 40, 40)
            if vision.victim_position is not None:
                x, y = vision.victim_position
                cv2.circle(show, (x, y), 16, (255, 0, 255), 2)
                label = vision.victim_type or "?"
                if vision.victim_distance_mm is not None:
                    label += f" {vision.victim_distance_mm:.0f}mm"
                if vision.victim_diameter_px is not None:
                    label += f" d={vision.victim_diameter_px:.0f}px"
                cv2.putText(
                    show, label, (x + 18, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 0, 255), 2,
                )
            return show

        # ========== NOVO MODO "k" com Canny adaptativo e imagem inteira ==========
        if mode == "k":
            # Usa a imagem inteira e Canny adaptativo (igual ao detector)
            bgr = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            median = np.median(gray)
            lower = int(max(0, 0.66 * median))
            upper = int(min(255, 1.33 * median))
            edges = cv2.Canny(gray, lower, upper)
            edges = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=1)
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
            canvas = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            # Desenha o contorno do obstáculo, se encontrado
            if vision.obstacle and vision.obstacle_bbox is not None:
                x, y, bw, bh = vision.obstacle_bbox
                cv2.rectangle(canvas, (x, y), (x + bw, y + bh), (0, 140, 255), 2)
                # Opcional: escrever métricas
                info = vision.obstacle_info
                if info:
                    cov = info.get('center_coverage', 0) * 100
                    hstd = info.get('h_std', 0)
                    sstd = info.get('s_std', 0)
                    txt = f"cov={cov:.0f}% Hstd={hstd:.1f} Sstd={sstd:.1f}"
                    cv2.putText(canvas, txt, (x, y - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 140, 255), 1)
            return canvas

        if mode == "d":
            show = frame.copy()
            gmask = cv2.inRange(hsv, objects.green_low, objects.green_high)
            rmask = cv2.bitwise_or(
                cv2.inRange(hsv, objects.red_low1, objects.red_high1),
                cv2.inRange(hsv, objects.red_low2, objects.red_high2),
            )
            show[gmask > 0] = (0, 180, 0)
            show[rmask > 0] = (0, 0, 200)
            return show

        # original sem overlay
        return frame.copy()

    @staticmethod
    def _gray_bgr(mask):
        return cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)