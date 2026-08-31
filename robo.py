#robo

import setup
import math
import time
from enum import Enum, auto
from encoder import Encoder
from odometria import Odometria
from pid import PID
from vision import Vision
from resgate import ControladorResgate


class Robo:

    def __init__(self):

        # Botão

        self.botao = setup.botao

        # Motores

        self.motorL = setup.motorL
        self.motorR = setup.motorR

        # Servos

        self.claw = setup.servo_claw
        self.lift = setup.servo_lift
        self.dump = setup.servo_dump

        # Encoders

        self.encoderL = Encoder(
            setup.encoderL_a,
            setup.encoderL_b
        )

        self.encoderR = Encoder(
            setup.encoderR_a,
            setup.encoderR_b
        )

        # Odometria

        self.odom = Odometria(
            setup.RAIO_RODA,
            setup.DISTANCIA_RODAS,
            setup.PULSOS_VOLTA
        )
        
        # Vision

        self.vision = Vision()
        self.resgate = ControladorResgate(self)

        # Memória

        self.memoria = {

            "ultima_curva": Curva.NENHUMA,

            "ultima_vitima": None,

            "ultimo_evento": Evento.NENHUM,

            "tempo_sem_linha": 0.0,

            "vitimas_vivas": 0,

            "vitimas_mortas": 0,

            "desvios": 0,

            "estado_desvio": None,

            "intersecoes": 0,

            "entrou_resgate": False,

            "tentativas": 0
        }

        # PID

        self._pid_encoder = PID(
            setup.KP_E,
            setup.KI_E,
            setup.KD_E,
            output_limits=(-0.35, 0.35),
            integral_limits=(-50, 50),
        )

        self._pid_linha = PID(
            setup.KP_L,
            setup.KI_L,
            setup.KD_L,
            output_limits=(-0.45, 0.45),
            integral_limits=(-2, 2),
        )

        # Controle

        self.ant_L = 0
        self.ant_R = 0

        self.erro_integral = 0
        self.erro_anterior = 0
        self._controle_anterior = time.monotonic()
        self._controle_dt = setup.CONTROLE_DT_MIN_S
        self._ultimo_erro_linha = 0.0
        self._frames_sem_linha = 0
        self._inicio_recuperacao_linha = None
        self._frames_obstaculo = 0
        self._movimento = None
        self._comando_motores = (0.0, 0.0)

        self.botao_pressionado = False

        self._ultimo_modo_linha = "suave"

    
    def atualizar(self):
        # Um único ciclo é dono da leitura de sensores e da visão.
        self.odom.atualizar(
            self.encoderL.ler(),
            self.encoderR.ler()
        )
        self.vision.update()
        self.atualizar_memoria()


    def atualizar_memoria(self):

        self.memoria["ultima_curva"] = self.curva_detectada()

        if self.tem_linha() and self.vision.center_error is not None:
            self._ultimo_erro_linha = self.vision.center_error
            self._frames_sem_linha = 0
            self._inicio_recuperacao_linha = None
        else:
            self._frames_sem_linha += 1
        self._frames_obstaculo = self._frames_obstaculo + 1 if self.vision.obstacle else 0
        self.memoria["ultimo_evento"] = self.evento()

        if self.tem_vitima():

            self.memoria["ultima_vitima"] = self.tipo_vitima()

        self.resgate.atualizar_observacao()


    def pose(self):

        return self.odom.pose()


    def vitima(self):

        return self.vision.victim_position


    def evento(self):

        # Eventos globais (maior prioridade)

        if self.tem_vermelho():
            return Evento.VERMELHO
        if self.tem_prata():
            return Evento.PRATA

        if self.tem_saida_resgate():
            return Evento.SAIDA_RESGATE

        # Eventos da sala de resgate

        if self.tem_vitima():
            return Evento.VITIMA

        # Eventos do percurso

        if self.tem_obstaculo() and self._frames_obstaculo >= setup.OBSTACULO_FRAMES_CONFIRMACAO:
            return Evento.OBSTACULO

        if self.tem_intersecao():
            return Evento.INTERSECAO

        if not self.tem_linha():
            return Evento.LINHA_PERDIDA

        return Evento.NENHUM


    def tem_linha(self):

        return self.vision.line_found


    def tem_intersecao(self):

        return self.memoria["ultima_curva"] != Curva.NENHUMA


    def tem_prata(self):

        return self.vision.silver


    def tem_vermelho(self):

        return self.vision.red


    def tem_obstaculo(self):

        return self.vision.obstacle

    def distancia_desde(self, ponto):
        return math.hypot(self.x - ponto[0], self.y - ponto[1])

    def lado_linha_obstaculo(self):
        """Classifica a linha visível à esquerda, direita ou atrás do objeto."""
        bbox = self.vision.obstacle_bbox
        mask = self.vision.line_mask
        if bbox is None or mask is None:
            return None

        x, y, w, h = bbox
        altura, largura = mask.shape
        margem = 15
        minimo = 35

        esquerda = self._pixels_pretos(mask, x - margem - w, y, x - margem, y + h)
        direita = self._pixels_pretos(mask, x + w + margem, y, x + 2 * w + margem, y + h)
        atras = self._pixels_pretos(mask, x, y + h + margem, x + w, y + h + 2 * h)

        if max(esquerda, direita) >= minimo:
            return "esquerda" if esquerda >= direita else "direita"
        if atras >= minimo:
            return "atras"
        return None

    def lado_livre_obstaculo(self):
        bbox = self.vision.obstacle_bbox
        if bbox is None or self.vision.frame is None:
            return "direita"
        x, _, w, _ = bbox
        centro = self.vision.frame.shape[1] // 2
        return "esquerda" if x + w // 2 > centro else "direita"

    def alinhar_borda_obstaculo(self, lado, vel=setup.VEL_DESVIO):
        bbox = self.vision.obstacle_bbox
        if bbox is None or self.vision.frame is None:
            return False

        x, _, w, _ = bbox
        centro = self.vision.frame.shape[1] // 2
        borda = x if lado == "esquerda" else x + w
        alvo = centro - setup.BORDA_OBSTACULO_ALVO_PX
        if lado == "direita":
            alvo = centro + setup.BORDA_OBSTACULO_ALVO_PX

        erro = borda - alvo
        if abs(erro) <= setup.TOLERANCIA_BORDA_OBSTACULO_PX:
            self.parar()
            return True
        if erro > 0:
            self.girar_direita(vel)
        else:
            self.girar_esquerda(vel)
        return False

    def curva_suave(self, lado, vel=setup.VEL_DESVIO):
        """Arco aberto: mantém o obstáculo e a linha no campo de visão."""
        interna = vel * 0.45
        if lado == "esquerda":
            self.set_motores(interna, vel)
        else:
            self.set_motores(vel, interna)

    def girar_para_lado(self, lado, vel=setup.VEL_DESVIO):
        if lado == "esquerda":
            self.girar_esquerda(vel)
        else:
            self.girar_direita(vel)

    def linha_perto(self):
        mask = self.vision.line_mask
        if mask is None:
            return False
        h, _ = mask.shape
        return int((mask[int(h * 0.78):, :] > 0).sum()) >= 80

    @staticmethod
    def _pixels_pretos(mask, x0, y0, x1, y1):
        h, w = mask.shape
        x0, x1 = max(0, x0), min(w, x1)
        y0, y1 = max(0, y0), min(h, y1)
        if x0 >= x1 or y0 >= y1:
            return 0
        return int((mask[y0:y1, x0:x1] > 0).sum())


    def tem_vitima(self):

        return self.vision.victim_position is not None


    def tipo_vitima(self):

        return self.vision.victim_type


    def tem_saida_resgate(self):

        return self.vision.black_exit

    def alinhar_faixa_prata(self, vel=setup.VEL_RESGATE):
        return self._alinhar_faixa(self.vision.silver_line, vel)

    def centralizar_saida_resgate(self, vel=setup.VEL_RESGATE):
        faixa = self.vision.black_exit_line
        if not faixa or not faixa["found"] or self.vision.frame is None:
            return False

        x, _ = faixa["position"]
        erro = x - self.vision.frame.shape[1] // 2
        if abs(erro) < 20:
            self.parar()
            return True
        if erro > 0:
            self.girar_direita(vel)
        else:
            self.girar_esquerda(vel)
        return False

    def saida_proxima(self):
        faixa = self.vision.black_exit_line
        if not faixa or not faixa["found"] or self.vision.frame is None:
            return False
        return faixa["y"] >= int(self.vision.frame.shape[0] * 0.80)

    def alinhar_linha(self, vel=setup.VEL_RESGATE):
        if not self.tem_linha():
            return False

        erro = self.heading
        if abs(erro) < math.radians(8):
            self.parar()
            return True
        if erro > 0:
            self.girar_direita(vel)
        else:
            self.girar_esquerda(vel)
        return False

    def _alinhar_faixa(self, faixa, vel):
        if not faixa or not faixa["found"] or faixa["angle"] is None:
            return False

        # A faixa deve ficar horizontal na imagem para o robô cruzá-la reto.
        erro = faixa["angle"]
        if erro > math.pi / 2:
            erro -= math.pi
        elif erro < -math.pi / 2:
            erro += math.pi

        if abs(erro) < math.radians(8):
            self.parar()
            return True
        if erro > 0:
            self.girar_esquerda(vel)
        else:
            self.girar_direita(vel)
        return False


    def tem_area_entrega(self, cor):
        return self._area_entrega(cor) is not None

    def centralizar_area_entrega(self, cor, vel=0.18):
        area = self._area_entrega(cor)
        if area is None or self.vision.frame is None:
            return False

        x, _ = area["position"]
        centro = self.vision.frame.shape[1] // 2
        erro = x - centro
        if abs(erro) < 20:
            self.parar()
            return True

        if erro > 0:
            self.girar_direita(vel)
        else:
            self.girar_esquerda(vel)
        return False

    def area_entrega_proxima(self, cor):
        area = self._area_entrega(cor)
        if area is None or self.vision.frame is None:
            return False
        return area["bottom_y"] >= int(self.vision.frame.shape[0] * 0.80)

    def _area_entrega(self, cor):
        if cor == "verde":
            return self.vision.green_area
        if cor == "vermelha":
            return self.vision.red_area
        raise ValueError("A cor da área deve ser 'verde' ou 'vermelha'.")

    def estado_pista(self):

        return {

            "evento": self.evento(),

            "curva": self.curva_detectada(),

            "erro": self.erro_linha,

            "heading": self.heading,

            "linha": self.tem_linha()
        }


    def dentro_resgate(self):

        return self.memoria["entrou_resgate"]


    def entrar_resgate(self):

        self.memoria["entrou_resgate"] = True


    def sair_resgate(self):

        self.memoria["entrou_resgate"] = False


    @property
    def erro_linha(self):
        # Nunca transformar linha perdida em "centralizada" (erro zero).
        return self.vision.center_error if self.vision.center_error is not None else self._ultimo_erro_linha


    @property
    def heading(self):

        return self.vision.heading


    @property
    def curvatura(self):

        return self.vision.curvature

    @property
    def distancia_vitima_mm(self):
        """Distancia estimada entre a bola e a camera, em milimetros."""
        return self.vision.victim_distance_mm

    @property
    def distancia_captura_mm(self):
        return setup.DISTANCIA_CAPTURA_MM

    def distancia_vitima(self):
        """Mantem uma API simples para a maquina de estados do resgate."""
        return self.distancia_vitima_mm


    @property
    def pista(self):

        return self.estado_pista()


    def curva_detectada(self):

        if self.vision.green_count == 2:
            return Curva.RETORNO

        if self.vision.green_left:
            return Curva.ESQUERDA

        if self.vision.green_right:
            return Curva.DIREITA

        return Curva.NENHUMA


    def percepcao(self):
        return {

            "linha": self.tem_linha(),

            "erro": self.erro_linha,

            "heading": self.heading,

            "curvatura": self.curvatura,

            "curva": self.curva_detectada(),

            "prata": self.tem_prata(),

            "vermelho": self.tem_vermelho(),

            "obstaculo": self.tem_obstaculo(),

            "vitima": self.tem_vitima(),

            "tipo_vitima": self.tipo_vitima(),

            "evento": self.evento(),

            "x": self.x,

            "y": self.y,

            "theta": self.theta
        }


    @property
    def x(self):
        return self.odom.x

    @property
    def y(self):
        return self.odom.y

    @property
    def theta(self):
        return self.odom.theta


    def parar(self):

        self.motorL.stop()
        self.motorR.stop()

    def iniciar_andar(self, mm, vel=setup.VEL_MED, re=False, timeout_s=10.0):
        """Inicia deslocamento sem bloquear o ciclo de sensores/Planner."""
        self._movimento = {"tipo": "andar", "inicio": (self.x, self.y), "alvo": abs(mm),
                           "vel": vel, "re": re, "inicio_t": time.monotonic(), "timeout": timeout_s}

    def iniciar_girar(self, graus, timeout_s=8.0):
        self._movimento = {"tipo": "girar", "alvo": self._normalizar_angulo(self.theta + math.radians(graus)),
                           "inicio_t": time.monotonic(), "timeout": timeout_s}

    def atualizar_movimento(self):
        """Executa uma única etapa e retorna True somente ao terminar/falhar."""
        m = self._movimento
        if m is None:
            return True
        if time.monotonic() - m["inicio_t"] > m["timeout"]:
            self.parar(); self._movimento = None; return True
        if m["tipo"] == "andar":
            if math.hypot(self.x - m["inicio"][0], self.y - m["inicio"][1]) >= m["alvo"]:
                self.parar(); self._movimento = None; return True
            (self.tras if m["re"] else self.frente)(m["vel"])
            return False
        erro = self._normalizar_angulo(m["alvo"] - self.theta)
        if abs(erro) < math.radians(1):
            self.parar(); self._movimento = None; return True
        vel = max(0.1, min(0.6, abs(erro) * 1.2))
        self.set_motores(vel, -vel) if erro > 0 else self.set_motores(-vel, vel)
        return False

    def abortar_movimento(self):
        self._movimento = None
        self.parar()

    
    def _corrigir_vel(self, vel=setup.VEL_MED):
        agora = time.monotonic()
        dt = agora - self._controle_anterior
        self._controle_anterior = agora
        self._controle_dt = dt
        atual_L = self.encoderL.ler()
        atual_R = self.encoderR.ler()

        delta_L = atual_L - self.ant_L
        delta_R = atual_R - self.ant_R

        self.ant_L = atual_L
        self.ant_R = atual_R

        erro = delta_L - delta_R
        
        correcao = self._pid_encoder.atualizar(erro, dt)

        vel_L = vel - correcao
        vel_R = vel + correcao

        vel_L = max(0, min(1, vel_L))
        vel_R = max(0, min(1, vel_R))

        return vel_L, vel_R

    
    def _corrigir_vel_linha(self, vel=setup.VEL_MED):
        # Verifica se há linha visível
        if not self.tem_linha():
            # Se linha perdida, usa último erro conhecido
            erro_abs = abs(self._ultimo_erro_linha)
        else:
            erro_abs = abs(self.vision.center_error)
        
        # Detecta modo de operação com histerese
        modo = self._determinar_modo_linha(erro_abs)
        
        if modo == "suave":
            return self._correcao_suave(vel)
        elif modo == "agressivo":
            return self._correcao_agressiva(vel)
        elif modo == "pivot":
            return self._correcao_pivot()
        else:  # crítico
            return self._correcao_critica()

    def _determinar_modo_linha(self, erro_abs):
        """Determina modo de operação com histerese para evitar oscilações."""
        # Verifica se já está em modo pivot
        if self._ultimo_modo_linha == "pivot":
            # Histerese: sai do pivot com limiar menor
            if erro_abs < setup.ERRO_LINHA_GRANDE - setup.HISTERESE_PIVOT:
                return self._classificar_erro_linha(erro_abs)
            else:
                return "pivot"
        else:
            return self._classificar_erro_linha(erro_abs)

    def _classificar_erro_linha(self, erro_abs):
        """Classifica o erro em categorias de correção."""
        if erro_abs < setup.ERRO_LINHA_PEQUENO:
            return "suave"
        elif erro_abs < setup.ERRO_LINHA_MEDIO:
            return "agressivo"
        elif erro_abs < setup.ERRO_LINHA_GRANDE:
            return "pivot"
        else:
            return "critico"

    def _correcao_suave(self, vel):
        """Correção suave para erros pequenos."""
        baseL, baseR = self._corrigir_vel(vel * setup.VEL_CORRECAO_SUAVE)
        
        erro = self.erro_linha * setup.PESO_ERRO_POS + self.vision.heading * setup.PESO_LOOKAHEAD
        correcao = self._pid_linha.atualizar(erro, self._controle_dt)
        
        velL = baseL - correcao
        velR = baseR + correcao
        
        return self._limitar_velocidades(velL, velR)

    def _correcao_agressiva(self, vel):
        """Correção agressiva para erros médios."""
        baseL, baseR = self._corrigir_vel(vel * setup.VEL_CORRECAO_AGRESSIVA)
        
        # Aumenta ganho do PID para correção mais forte
        erro = self.erro_linha * (setup.PESO_ERRO_POS * 1.5) + self.vision.heading * setup.PESO_LOOKAHEAD
        correcao = self._pid_linha.atualizar(erro, self._controle_dt)
        
        velL = baseL - correcao
        velR = baseR + correcao
        
        return self._limitar_velocidades(velL, velR)

    def _correcao_pivot(self):
        """Pivot turn para erros grandes."""
        # Determina direção do pivot baseado no erro
        if self.erro_linha > 0:  # linha à direita
            # Motor esquerdo para frente, direito para trás
            velL = self._calcular_vel_pivot(abs(self.erro_linha))
            velR = -velL
        else:  # linha à esquerda
            # Motor direito para frente, esquerdo para trás
            velR = self._calcular_vel_pivot(abs(self.erro_linha))
            velL = -velR
        
        self._ultimo_modo_linha = "pivot"
        return velL, velR

    def _correcao_critica(self):
        """Correção crítica para linha quase perdida."""
        # Usa último erro conhecido para determinar direção
        if self._ultimo_erro_linha >= 0:
            # Linha estava à direita
            velL = setup.VEL_PIVOT_MAX
            velR = -setup.VEL_PIVOT_MAX
        else:
            # Linha estava à esquerda
            velL = -setup.VEL_PIVOT_MAX
            velR = setup.VEL_PIVOT_MAX
        
        self._ultimo_modo_linha = "pivot"
        return velL, velR

    def _calcular_vel_pivot(self, erro_abs):
        """Calcula velocidade do pivot proporcional ao erro."""
        # Normaliza erro entre ERRO_LINHA_GRANDE e ERRO_LINHA_CRITICO
        erro_normalizado = (erro_abs - setup.ERRO_LINHA_GRANDE) / (setup.ERRO_LINHA_CRITICO - setup.ERRO_LINHA_GRANDE)
        erro_normalizado = max(0, min(1, erro_normalizado))
        
        # Interpola entre VEL_PIVOT_MIN e VEL_PIVOT_MAX
        return setup.VEL_PIVOT_MIN + erro_normalizado * (setup.VEL_PIVOT_MAX - setup.VEL_PIVOT_MIN)

    def _limitar_velocidades(self, velL, velR):
        """Garante que velocidades estejam dentro dos limites do hardware."""
        velL = max(setup.VEL_MIN_MOTOR, min(setup.VEL_MAX_MOTOR, velL))
        velR = max(setup.VEL_MIN_MOTOR, min(setup.VEL_MAX_MOTOR, velR))
        return velL, velR


    def _normalizar_angulo(self, a):

        while a > math.pi:
            a -= 2*math.pi

        while a < -math.pi:
            a += 2*math.pi

        return a
    
    def iniciar(self):
        self.botao.when_pressed = self._botao_pressionado

    def _botao_pressionado(self):
        self.botao_pressionado = True

    def set_motores(self, velL, velR):

        # Guarda o último comando para a telemetria. Os valores vão de -1
        # (ré) a 1 (frente) e representam exatamente o que foi enviado.
        self._comando_motores = (velL, velR)

        if velL >= 0:
            self.motorL.forward(velL)
        else:
            self.motorL.backward(-velL)

        if velR >= 0:
            self.motorR.forward(velR)
        else:
            self.motorR.backward(-velR)


    def frente(self, vel=setup.VEL_MED):

        vel_L, vel_R = self._corrigir_vel(vel)

        self.set_motores(vel_L, vel_R)


    def tras(self, vel=setup.VEL_MED):

        vel_L, vel_R = self._corrigir_vel(vel)

        self.set_motores(-vel_L, -vel_R)


    def girar(self, graus):

        alvo = self.theta + math.radians(graus)

        while True:

            self.atualizar()

            erro = self._normalizar_angulo (alvo - self.theta)

            if abs(erro) < math.radians(1):
                break

            vel = abs(erro) * 1.2

            vel = max(0.1, min(0.6, vel))

            if erro > 0:

                self.set_motores(vel, -vel)

            else:

                self.set_motores(-vel, vel)

        self.parar()


    def girar_direita(self, vel):
        
        self.set_motores(vel, -vel)

    
    def girar_esquerda(self, vel):

        self.set_motores(-vel, vel)


    def andar(self, mm, vel=setup.VEL_MED):
        
        inicio = time.time()
        x0 = self.x
        y0 = self.y

        while True:

            self.atualizar()

            dx = self.x - x0
            dy = self.y - y0

            distancia = math.sqrt(dx**2 + dy**2)

            if distancia >= mm:
                break

            self.frente(vel)

            if time.time()-inicio > 10:
                break

        self.parar()


    def andar_re(self, mm, vel=setup.VEL_MED):
        """Percorre uma distância de ré usando a odometria."""
        inicio = time.time()
        x0 = self.x
        y0 = self.y

        while True:
            self.atualizar()
            distancia = math.hypot(self.x - x0, self.y - y0)
            if distancia >= mm or time.time() - inicio > 10:
                break
            self.tras(vel)

        self.parar()

    def seguir_linha(self, vel = setup.VEL_MED):
        if not self.tem_linha():
            if self._frames_sem_linha >= setup.LINHA_FRAMES_RECUPERAR:
                return self.recuperar_linha()
            vel *= 0.45 if self._frames_sem_linha >= setup.LINHA_FRAMES_REDUZIR else 0.7
        
        vel_L, vel_R = self._corrigir_vel_linha(vel)
        self.set_motores(vel_L, vel_R)

    def status_linha(self):
        """Resumo legível do acompanhamento da linha no frame atual."""
        if not self.tem_linha() or self.vision.center_error is None:
            lado = "desconhecido"
            deslocamento = 0.0
            leitura = "não encontrei a linha"
        else:
            erro = self.vision.center_error
            deslocamento = abs(erro) * 100
            if abs(erro) < 0.05:
                lado = "no centro"
            elif erro < 0:
                lado = "à esquerda"
            else:
                lado = "à direita"
            leitura = f"linha {lado} ({deslocamento:.0f}% da largura da câmera)"

        vel_l, vel_r = self._comando_motores
        return (
            f"Lendo linha: {leitura}. Objetivo: centralizar a linha; "
            f"motores E={vel_l:+.2f}, D={vel_r:+.2f}."
        )

    def recuperar_linha(self):
        """Busca limitada; devolve False após timeout para o Planner parar."""
        if self._inicio_recuperacao_linha is None:
            self._inicio_recuperacao_linha = time.monotonic()
        if time.monotonic() - self._inicio_recuperacao_linha > setup.TEMPO_MAX_RECUPERAR_LINHA_S:
            self.parar()
            return False
        # Busca no sentido do último erro conhecido, mantendo baixa velocidade.
        lado = 1 if self._ultimo_erro_linha >= 0 else -1
        self.set_motores(0.12 * lado, -0.12 * lado)
        return True


    def centralizar_vitima(self, vel=setup.VEL_MED):

        if self.vision.victim_position is None:
            return False


        x,y = self.vision.victim_position


        largura = self.vision.frame.shape[1]

        centro = largura // 2


        erro = x - centro



        if abs(erro) < 15:
            self.parar()
            return True



        if erro > 0:

            self.girar_direita(vel)

        else:

            self.girar_esquerda(vel)


        return False


    def avancar_ate_linha(self, limite_mm, vel=0.20):
        """Avança até reencontrar a linha, sem ultrapassar o limite seguro."""
        inicio = (self.x, self.y)
        while math.hypot(self.x - inicio[0], self.y - inicio[1]) < limite_mm:
            self.atualizar()
            if self.tem_linha():
                self.parar()
                return self.alinhar_linha(vel)
            self.frente(vel)
        self.parar()
        return False

    def procurar_linha(self, direcao=1, passos=8, passo_graus=15):
        """Varre a visão em arco e confirma o alinhamento ao reencontrar a linha."""
        for _ in range(passos):
            self.atualizar()
            if self.tem_linha():
                return self.alinhar_linha()
            self.girar(direcao * passo_graus)
        self.parar()
        return False

    def desviar(self):
        """Contorna o obstáculo pelo lado que permite recuperar a linha."""
        self.parar()
        self.andar_re(setup.RECUO_OBSTACULO_MM, setup.VEL_RESGATE)

        # A margem lateral cobre a largura máxima (120 mm) e evita a borda.
        for lado in (1, -1):
            self.girar(90 * lado)
            self.andar(setup.DESVIO_LATERAL_MM, setup.VEL_RESGATE)
            self.girar(-90 * lado)

            # Primeiro passa do comprimento máximo do objeto e procura a linha.
            if self.avancar_ate_linha(setup.DESVIO_AVANCO_MM):
                return True

            # Se ela não estiver adiante, cruza de volta para o traçado esperado.
            self.girar(-90 * lado)
            if self.avancar_ate_linha(setup.DESVIO_RETORNO_MM):
                return True

            if self.procurar_linha(lado):
                return True

        self.parar()
        return False


    def garra(self, estado = "open"):
        if estado == "open":
            self.claw.min()
        if estado == "closed":
            self.claw.max()


    def alavanca(self, altura = "down"):
        if altura == "up":
            self.lift.value = (setup.angulo_garra / 90) -1
        if altura == "down":
            self.lift.max()


    def cacamba(self, estado = "down"):
        if estado == "up":
            self.dump.mid()
        if estado == "down":
            self.dump.min()


    def capturar_vitima(self):
        """Executa somente a sequência mecânica de captura da bola."""
        self.parar()
        self.garra("open")
        self.alavanca("down")
        self.garra("closed")
        time.sleep(0.5)
        self.alavanca("up")
        self.garra("open")

    def entregar_vitima(self):
        """Entra de ré na área para despejar pela caçamba traseira."""
        self.parar()
        self.girar(180)
        self.andar_re(setup.DISTANCIA_RE_ENTREGA_MM, setup.VEL_ENTREGA)
        self.cacamba("up")
        time.sleep(setup.TEMPO_BASCULA_S)
        self.cacamba("down")

    def executar_resgate(self):
        self.resgate.executar()


    def resgate_finalizado(self):
        return self.resgate.finalizado


class Evento(Enum):

    NENHUM = auto()

    OBSTACULO = auto()

    INTERSECAO = auto()

    PRATA = auto()

    LINHA_PERDIDA = auto()

    VERMELHO = auto()

    VITIMA = auto()

    SAIDA_RESGATE = auto()


class Curva(Enum):

    NENHUMA = auto()

    ESQUERDA = auto()

    DIREITA = auto()

    RETORNO = auto()

    
