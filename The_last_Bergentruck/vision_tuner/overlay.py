# overlay — desenha no frame o que a Vision decidiu (além do Debug interno).

import cv2


class Overlay:

    def draw(self, frame, vision, diagnostics):
        img = vision.debugger.draw(frame, vision)

        if vision.obstacle and vision.obstacle_bbox is not None:
            x, y, w, h = vision.obstacle_bbox
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 140, 255), 2)
            # Adiciona métricas
            info = vision.obstacle_info
            if info:
                cov = info.get('center_coverage', 0) * 100
                hstd = info.get('h_std', 0)
                sstd = info.get('s_std', 0)
                label = f"cov={cov:.0f}% Hstd={hstd:.1f} Sstd={sstd:.1f}"
                cv2.putText(img, label, (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 140, 255), 1)

        if vision.green_area is not None:
            gx, gy = vision.green_area["position"]
            cv2.circle(img, (gx, gy), 12, (0, 255, 0), 2)
            cv2.putText(
                img, "DEST VERDE", (gx + 14, gy),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
            )

        if vision.red_area is not None:
            rx, ry = vision.red_area["position"]
            cv2.circle(img, (rx, ry), 12, (0, 0, 255), 2)
            cv2.putText(
                img, "DEST VERMELHO", (rx + 14, ry),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1,
            )

        if vision.silver_line and vision.silver_line.get("found"):
            pos = vision.silver_line.get("position")
            if pos:
                cv2.circle(img, pos, 8, (200, 200, 200), -1)

        if vision.black_exit_line and vision.black_exit_line.get("found"):
            pos = vision.black_exit_line.get("position")
            if pos:
                cv2.circle(img, pos, 8, (80, 80, 80), -1)

        cam = diagnostics.camera
        cv2.putText(
            img,
            f"{cam.width}x{cam.height}  {cam.fps:.1f} fps  "
            f"{diagnostics.system.processing_ms:.1f} ms",
            (10, img.shape[0] - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 255),
            1,
        )
        return img