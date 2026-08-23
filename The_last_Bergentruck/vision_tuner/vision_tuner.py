#!/usr/bin/env python3
"""
vision_tuner — vê o que o robô vê e calibra a visão no PC.

Rode a partir da raiz do projeto ou desta pasta:

  python vision_tuner/vision_tuner.py
  python vision_tuner/vision_tuner.py --camera 1

Usa o mesmo pipeline de vision/ (linha, verdes, fitas, obstáculo, vítimas)
e os valores de setup.py (focal, área de destino, resolução da câmera).

Teclas:
  o  overlay completo (decisões do robô)
  n  frame original
  l  máscara da linha
  g  máscara verde
  r  máscara vermelha
  s  máscara prata (entrada)
  b  máscara preta (saída)
  v  vítimas
  k  obstáculo (bordas)
  d  destinos verde/vermelho
  h  liga/desliga ajuda
  c  HSV do centro
  p  imprime faixas HSV no terminal
  +/–  ajusta DISTANCIA_FOCAL_PX
  q  sair

Clique ou mova o mouse sobre a imagem para ler HSV do pixel.
"""

import argparse
import os
import sys

# garante imports relativos desta pasta
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from app import VisionTunerApp


def main():
    parser = argparse.ArgumentParser(description="Calibrador de visão OBR")
    parser.add_argument(
        "--camera", type=int, default=None,
        help="Índice da câmera (padrão: setup.CAMERA_ID)",
    )
    args = parser.parse_args()
    app = VisionTunerApp(camera_id=args.camera)
    app.run()


if __name__ == "__main__":
    main()
