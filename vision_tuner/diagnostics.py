# diagnostics — estado legível do que a Vision detectou neste frame.

from dataclasses import dataclass
import time


@dataclass
class CameraInfo:
    width: int = 0
    height: int = 0
    fps: float = 0.0
    connected: bool = False


@dataclass
class LineInfo:
    found: bool = False
    error: float = 0.0
    heading: float = 0.0
    curvature: float = 0.0
    skeleton_points: int = 0


@dataclass
class ObjectInfo:
    green_left: bool = False
    green_right: bool = False
    green_count: int = 0
    red: bool = False
    silver: bool = False
    black_exit: bool = False
    obstacle: bool = False
    green_area: bool = False
    red_area: bool = False


@dataclass
class VictimInfo:
    found: bool = False
    type: str = None
    position: tuple = None
    diameter_px: float = None
    distance_mm: float = None


@dataclass
class SystemInfo:
    frame_number: int = 0
    processing_ms: float = 0.0
    mode: str = "overlay"


class Diagnostics:

    def __init__(self):
        self.camera = CameraInfo()
        self.line = LineInfo()
        self.objects = ObjectInfo()
        self.victims = VictimInfo()
        self.system = SystemInfo()
        self._t0 = time.perf_counter()
        self._frames = 0
        self._fps_acc = 0.0

    def update(self, vision, mode: str, processing_ms: float):
        self._update_camera(vision)
        self._update_line(vision)
        self._update_objects(vision)
        self._update_victims(vision)
        self._update_system(mode, processing_ms)

    def _update_camera(self, vision):
        frame = vision.frame
        connected = frame is not None
        self.camera.connected = connected
        if connected:
            h, w = frame.shape[:2]
            self.camera.width = w
            self.camera.height = h

        self._frames += 1
        now = time.perf_counter()
        dt = now - self._t0
        if dt >= 0.5:
            self.camera.fps = self._frames / dt
            self._frames = 0
            self._t0 = now

    def _update_line(self, vision):
        self.line.found = bool(vision.line_found)
        self.line.error = float(vision.center_error or 0)
        self.line.heading = float(vision.heading or 0)
        self.line.curvature = float(vision.curvature or 0)
        self.line.skeleton_points = len(vision.skeleton or [])

    def _update_objects(self, vision):
        self.objects.green_left = bool(vision.green_left)
        self.objects.green_right = bool(vision.green_right)
        self.objects.green_count = int(vision.green_count or 0)
        self.objects.red = bool(vision.red)
        self.objects.silver = bool(vision.silver)
        self.objects.black_exit = bool(vision.black_exit)
        self.objects.obstacle = bool(vision.obstacle)
        self.objects.green_area = vision.green_area is not None
        self.objects.red_area = vision.red_area is not None

    def _update_victims(self, vision):
        pos = vision.victim_position
        self.victims.found = pos is not None
        self.victims.type = vision.victim_type
        self.victims.position = pos
        self.victims.diameter_px = vision.victim_diameter_px
        self.victims.distance_mm = vision.victim_distance_mm

    def _update_system(self, mode, processing_ms):
        self.system.frame_number += 1
        self.system.processing_ms = processing_ms
        self.system.mode = mode
