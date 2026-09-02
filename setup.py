# setup — constantes e (no Pi) hardware GPIO.
# No PC, gpiozero pode existir sem pinos: só as constantes ficam disponíveis.

import warnings

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from gpiozero import Motor, Servo, Button

        # botão

        botao = Button(2) #certo

        # ponte H

        motorL = Motor(
            forward=10,
            backward=9, # a testar
            enable=11,
        )

        motorR = Motor(
            forward=27,
            backward=22, # a testar
            enable=17,
        )

        # servos

        servo_claw = Servo(5) #se não tiver certo, troca com o de baixo
        servo_lift = Servo(4) #se não tiver certo, troca com o de cima
        servo_dump = Servo(3) #certo

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
    Motor = Servo = None
    botao = None
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
DISTANCIA_RODAS = 180
# NECESSITA CALIBRAÇÃO FÍSICA: pulsos por volta completa da roda no modo
# atual do Encoder (canal A em borda de subida, sem quadrature x4).
PULSOS_VOLTA = 550

# velocidades

VEL_MIN = 0.1
VEL_MED = 0.15
VEL_MAX = 0.3

# PID encoder

KP_E = 0.001
KI_E = 0
KD_E = 0

CONTROLE_DT_MIN_S = 0.005
# Intervalo entre mensagens de telemetria. Não altera o controle dos motores.
TELEMETRIA_INTERVALO_S = 0.5
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

# PID linha — escala real: erro combinado ~[-1, 1]; a correção precisa
# chegar perto da velocidade base. KP=0.004 dava 0.0009 (0.6% da base).
KP_L = 0.25        # comece aqui; suba se ainda cortar curva por fora
KI_L = 0.0
KD_L = 0.05        # amortece; se tremer na reta, reduza

PESO_ERRO_POS = 0.70
PESO_LOOKAHEAD = 0.25   # heading em rad (~±0.9): antecipa a curva

GIRO_MAX_FRAC = 0.85    # correção ≤ 85% da vel: diferença entre rodas nunca
                        # passa de ~1.7x a velocidade -> nunca pivô acidental
FRENO_CURVA_FRAC = 0.35 # freia no máx 35% (era 55%: freava demais e virava pivô)
FILTRO_ERRO_ALFA = 0.55 # 0 = sem filtro; 0.5-0.6 mata ruído sem atrasar muito
TRIM_ENCODER_MAX = 0.03 # teto do PID de encoders DURANTE a linha (ver abaixo)

SENTIDO_CORRECAO = 1     # -1 se o teste de direção mostrar fugindo da linha
ERRO_PERDIDA_GIRA = 0.40 # perdeu linha com erro >= isso: é curva, gira JÁ

# Camera (vision_tuner / Vision)
CAMERA_ID = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
