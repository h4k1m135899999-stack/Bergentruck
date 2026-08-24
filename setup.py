# setup — constantes e (no Pi) hardware GPIO.
# No PC, gpiozero pode existir sem pinos: só as constantes ficam disponíveis.

import warnings

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from gpiozero import Motor, Servo, RotaryEncoder

        # ponte H

        motorL = Motor(
            forward=10,
            backward=9,
            enable=11,
        )

        motorR = Motor(
            forward=22,
            backward=27,
            enable=17,
        )

        # servos

        servo_claw = Servo(3)
        servo_lift = Servo(4)
        servo_dump = Servo(5)

    # utilização
    # motorR.forward()
    # motorL.backward()
    # motorR.stop()
    # motorL.forward(speed=0.5) -> 50% da potência

    # encoder

    encoderL_a = 19
    encoderL_b = 26

    encoderR_a = 6
    encoderR_b = 13

except Exception:
    # Ambiente sem GPIO (ex.: calibrar visão no PC).
    Motor = Servo = RotaryEncoder = None
    motorL = motorR = None
    encoderL_a = encoderL_b = None
    encoderR_a = encoderR_b = None
    servo_claw = servo_lift = servo_dump = None

angulo_garra = 45

# utilização
# servo_claw.min()
# servo_lift.mid()
# servo_dump.max()

# odometria

RAIO_RODA = 32.5
DISTANCIA_RODAS = 166
# NECESSITA CALIBRAÇÃO FÍSICA: pulsos por volta completa da roda no modo
# atual do Encoder (canal A em borda de subida, sem quadrature x4).
PULSOS_VOLTA = 550

# velocidades

VEL_MIN = 0.4
VEL_MED = 0.7
VEL_MAX = 1.0

# PID encoder

KP_E = 0.005
KI_E = 0
KD_E = 0

PESO_ERRO_POS = 0.5
# center_error agora é normalizado em [-1, 1]; heading permanece em radianos.
PESO_LOOKAHEAD = 0.5

CONTROLE_DT_MIN_S = 0.005
LINHA_FRAMES_REDUZIR = 3
LINHA_FRAMES_RECUPERAR = 12
TEMPO_MAX_RECUPERAR_LINHA_S = 6.0
OBSTACULO_FRAMES_CONFIRMACAO = 2
OBSTACULO_FRAMES_SAIDA = 3
LINHA_FRAMES_CONFIRMACAO = 3

# Camera / bolas da sala de resgate (calibrar na resolucao usada pela camera).
# Para calibrar DISTANCIA_FOCAL_PX: focal_px = largura_px_da_bola *
# distancia_real_mm / DIAMETRO_BOLA_MM.
DIAMETRO_BOLA_MM = 50.0
DISTANCIA_FOCAL_PX = 500.0
DISTANCIA_CAPTURA_MM = 80.0

# Entrega: a caçamba fica atrás. O robô vira e entra de ré na área antes de
# levantar a caçamba. Ajustar estas distâncias na arena real.
DISTANCIA_RE_ENTREGA_MM = 90.0
VEL_ENTREGA = 0.18
TEMPO_BASCULA_S = 1.0

# Área colorida deve ocupar pelo menos esta quantidade de pixels para ser
# considerada um destino, evitando confundir as marcações verdes da pista.
AREA_DESTINO_MIN_PX = 1500

# Entrada e saída da sala de resgate.
VEL_RESGATE = 0.20
AVANCO_ENTRADA_RESGATE_MM = 300.0
TEMPO_MAX_ENTRADA_RESGATE_S = 8.0
AVANCO_BUSCA_SAIDA_MM = 120.0
TENTATIVAS_BUSCA_SAIDA = 3
AVANCO_ATE_SAIDA_MM = 250.0
AVANCO_TESTE_SAIDA_MM = 80.0

# Margens para desviar do maior obstáculo previsto (120 x 250 mm).
RECUO_OBSTACULO_MM = 80.0
DESVIO_LATERAL_MM = 180.0
DESVIO_AVANCO_MM = 320.0
DESVIO_RETORNO_MM = 220.0

# Desvio visual suave; as distâncias em pixels dependem da resolução da câmera.
VEL_DESVIO = 0.18
BORDA_OBSTACULO_ALVO_PX = 110
TOLERANCIA_BORDA_OBSTACULO_PX = 18
AVANCO_SAIDA_LINHA_MM = 50.0
AVANCO_MAX_DESVIO_MM = 400.0
TEMPO_MAX_DESVIO_S = 12.0

# PID linha

KP_L = 0.005
KI_L = 0
KD_L = 0

# Camera (vision_tuner / Vision)
CAMERA_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
