# controls — teclado / mouse do vision_tuner.

import cv2


class Controls:

    def __init__(self, window_name: str):
        self.window_name = window_name
        self._app = None

    def bind(self, app):
        self._app = app
        cv2.setMouseCallback(self.window_name, self._on_mouse)

    def update(self, app) -> bool:
        """Processa tecla. Retorna False se deve sair."""
        key = cv2.waitKey(1) & 0xFF
        if key == 255 or key == 0:
            return True

        if key in (ord("q"), 27):  # q ou ESC
            return False

        char = chr(key) if 32 <= key < 127 else ""

        if char in app.masks.MODE_NAMES:
            app.mode = char
            print(f"Modo: {app.masks.MODE_NAMES[char]}")
            return True

        if char == "h":
            app.ui.show_help = not app.ui.show_help
            return True

        if char == "c":
            app.sample_center_hsv()
            return True

        if char == "p":
            app.print_hsv_ranges()
            return True

        if char in ("+", "="):
            app.nudge_focal(+10)
            return True

        if char in ("-", "_"):
            app.nudge_focal(-10)
            return True

        return True

    def _on_mouse(self, event, x, y, flags, param):
        if self._app is None:
            return
        if event == cv2.EVENT_LBUTTONDOWN or event == cv2.EVENT_MOUSEMOVE:
            self._app.sample_mouse_hsv(x, y)
