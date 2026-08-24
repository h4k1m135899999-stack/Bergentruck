# app — loop principal do calibrador de visão.

import os
import sys
import time

import cv2

# permite importar vision/ e setup.py a partir da raiz do projeto
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import setup
from vision import Vision

from diagnostics import Diagnostics
from overlay import Overlay
from masks import MaskViews
from ui import UI
from controls import Controls


WINDOW = "Vision Tuner — The_last_Bergentruck"


class VisionTunerApp:

    def __init__(self, camera_id=None):
        camera_id = setup.CAMERA_ID if camera_id is None else camera_id
        self.vision = Vision(camera_id=camera_id)
        self.diagnostics = Diagnostics()
        self.overlay = Overlay()
        self.masks = MaskViews()
        self.ui = UI()
        self.controls = Controls(WINDOW)
        self.mode = "o"
        self.running = True

    def sample_mouse_hsv(self, x, y):
        hsv = self.vision.hsv
        if hsv is None:
            return
        h_img, w_img = hsv.shape[:2]
        if not (0 <= x < w_img and 0 <= y < h_img):
            return
        h, s, v = hsv[y, x]
        self.ui.mouse_hsv = (x, y, int(h), int(s), int(v))

    def sample_center_hsv(self, announce=True):
        hsv = self.vision.hsv
        if hsv is None:
            return
        cy, cx = hsv.shape[0] // 2, hsv.shape[1] // 2
        h, s, v = hsv[cy, cx]
        self.ui.center_hsv = (int(h), int(s), int(v))
        self.ui.mouse_hsv = None
        if announce:
            print(f"HSV centro: H={h} S={s} V={v}")

    def nudge_focal(self, delta):
        focal = self.vision.distance.distancia_focal_px + delta
        focal = max(50.0, focal)
        self.vision.distance.distancia_focal_px = focal
        setup.DISTANCIA_FOCAL_PX = focal
        print(
            f"DISTANCIA_FOCAL_PX = {focal:.1f}  "
            "(copie para setup.py quando calibrar)"
        )

    def print_hsv_ranges(self):
        line = self.vision.line
        obj = self.vision.objects
        vic = self.vision.victims
        print("\n=== HSV atuais (cole nos detectores / setup) ===")
        print(f"LINE   low={line.low.tolist()}  high={line.high.tolist()}")
        print(f"GREEN  low={obj.green_low.tolist()}  high={obj.green_high.tolist()}")
        print(f"RED1   low={obj.red_low1.tolist()}  high={obj.red_high1.tolist()}")
        print(f"RED2   low={obj.red_low2.tolist()}  high={obj.red_high2.tolist()}")
        print(f"SILVER low={obj.silver_low.tolist()}  high={obj.silver_high.tolist()}")
        print(f"BLACK  low={obj.black_low.tolist()}  high={obj.black_high.tolist()}")
        print(
            f"VIC_S  low={vic.silver_low.tolist()}  "
            f"high={vic.silver_high.tolist()}"
        )
        print(
            f"VIC_D  low={vic.dark_low.tolist()}  "
            f"high={vic.dark_high.tolist()}"
        )
        print(f"DISTANCIA_FOCAL_PX = {self.vision.distance.distancia_focal_px}")
        print(f"AREA_DESTINO_MIN_PX = {setup.AREA_DESTINO_MIN_PX}")
        print("================================================\n")

    def update(self):
        t0 = time.perf_counter()
        ok = self.vision.update()
        ms = (time.perf_counter() - t0) * 1000.0
        if not ok:
            return False
        self.diagnostics.update(self.vision, self.mode, ms)
        if self.ui.mouse_hsv is None:
            self.sample_center_hsv(announce=False)
        return True

    def draw(self):
        if self.mode == "o":
            img = self.overlay.draw(
                self.vision.frame, self.vision, self.diagnostics
            )
        else:
            img = self.masks.render(self.vision, self.mode)

        mode_name = self.masks.MODE_NAMES.get(self.mode, self.mode)
        img = self.ui.draw(img, self.diagnostics, mode_name)
        cv2.imshow(WINDOW, img)

    def run(self):
        print("Vision Tuner iniciado.")
        print("Teclas: o n l g r s b v k d | h ajuda | p HSV | +/- focal | q sair")
        print(f"Camera {setup.CAMERA_ID}  "
              f"{setup.FRAME_WIDTH}x{setup.FRAME_HEIGHT}")
        print(
            f"Focal inicial: {setup.DISTANCIA_FOCAL_PX} px  "
            f"(bola {setup.DIAMETRO_BOLA_MM} mm)"
        )

        cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
        self.controls.bind(self)

        try:
            while self.running:
                if not self.update():
                    print("Falha ao ler frame da camera.")
                    break
                self.draw()
                if not self.controls.update(self):
                    break
        finally:
            self.vision.release()
            cv2.destroyAllWindows()
