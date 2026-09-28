"""Camera pipeline dedicated to line following."""

import time

import cv2
import setup
from .line import LineDetector


class Vision:
    def __init__(self, camera_id=None, width=None, height=None):
        self.width = setup.FRAME_WIDTH if width is None else width
        self.height = setup.FRAME_HEIGHT if height is None else height
        camera_id = setup.CAMERA_ID if camera_id is None else camera_id

        self.cap = cv2.VideoCapture(camera_id, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir a câmera {camera_id}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FPS, setup.CAMERA_FPS)
        actual = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                  int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        self.resize_needed = actual != (self.width, self.height)
        print(f"Câmera Odisseu: {actual[0]}x{actual[1]} (solicitado {self.width}x{self.height})")

        self.line = LineDetector()
        self.frame = None
        self.line_found = False
        self.center_error = None
        self.heading = 0.0
        self.curvature = 0.0
        self.skeleton = []
        self.line_mask = None
        self.line_confidence = 0.0
        self.fps = 0.0
        self._last_time = None

    def update(self):
        ok, frame = self.cap.read()
        if not ok:
            return False
        if self.resize_needed:
            frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)

        # Processa a imagem em tons de cinza, suficiente para a faixa preta e
        # mais barato que converter cada frame para HSV.
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        result = self.line.detect(gray)
        self.frame = frame
        self.line_found = result["found"]
        self.center_error = result["error"]
        self.heading = result["heading"]
        self.curvature = result["curvature"]
        self.skeleton = result["skeleton"]
        self.line_mask = result["mask"]
        self.line_confidence = result["confidence"]

        now = time.perf_counter()
        if self._last_time is not None:
            dt = now - self._last_time
            if dt > 0:
                instant = 1.0 / dt
                self.fps = instant if self.fps == 0 else 0.8 * self.fps + 0.2 * instant
        self._last_time = now
        return True

    def release(self):
        if self.cap is not None:
            self.cap.release()
