"""Hardware pins and line-following tuning for Odisseu."""

import warnings

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from gpiozero import Motor, Button

        botao = Button(2)
        motorL = Motor(forward=10, backward=9, enable=11)
        motorR = Motor(forward=27, backward=22, enable=17)
        encoderL_a, encoderL_b = 19, 26
        encoderR_a, encoderR_b = 6, 13
except Exception:
    Motor = Button = None
    botao = motorL = motorR = None
    encoderL_a = encoderL_b = encoderR_a = encoderR_b = None

# Encoders: uma contagem por borda de subida no canal A.
RAIO_RODA = 32.5
DISTANCIA_RODAS = 180
PULSOS_VOLTA = 550

VEL_MED = 0.22

# Controle de linha: erro combinado normalizado entre aproximadamente -1 e 1.
KP_L = 0.2
KI_L = 0.0
KD_L = 0.0
PESO_ERRO_POS = 0.70
PESO_LOOKAHEAD = 0.38
GIRO_MAX_FRAC = 1.20
GIRO_REVERSO_MAX_FRAC = 0.35
FRENO_CURVA_FRAC = 0.18
FILTRO_ERRO_ALFA = 0.72
SENTIDO_CORRECAO = 1  # Mude para -1 se o teste físico mostrar correção invertida.
ERRO_PERDIDA_GIRA = 0.40

LINHA_FRAMES_REDUZIR = 3
LINHA_FRAMES_RECUPERAR = 12
TEMPO_MAX_RECUPERAR_LINHA_S = 6.0
TELEMETRIA_INTERVALO_S = 0.5

# A câmera e o OpenCV ainda limitam o FPS; o pipeline solicita 60 Hz quando suportado.
CAMERA_ID = 0
CAMERA_FPS = 60
FRAME_WIDTH = 160
FRAME_HEIGHT = 120
