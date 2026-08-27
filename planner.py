# planner

from abc import ABC, abstractmethod
from enum import Enum, auto
import math
import time
import setup

from robo import Evento, Curva
from desvio import DesvioInteligente


class EstadoID(Enum):

    START = auto()

    SEGUIR_LINHA = auto()

    DESVIAR = auto()

    INTERSECAO = auto()

    ENTRAR_RESGATE = auto()

    RESGATE = auto()

    SAIR_RESGATE = auto()

    STOP = auto()


class Contexto:

    def __init__(self):

        self.debug = True

        self.estado_anterior = None

        self.inicio_estado = time.time()


class Estado(ABC):

    ID = None

    def __init__(self, planner):

        self.planner = planner
        self.robo = planner.robo

    def entrar(self):
        pass

    @abstractmethod
    def executar(self):
        pass

    def sair(self):
        pass


class Planner:

    def __init__(self, robo):

        self.robo = robo

        self.contexto = Contexto()

        self.estado = Start(self)

        self._ultimo_status = 0.0

        self.estado.entrar()


    def update(self):

        self.robo.atualizar()

        self.estado.executar()


    def mudar_estado(self, novo_estado):

        self.estado.sair()

        self.contexto.estado_anterior = self.estado.ID

        self.estado = novo_estado(self)

        self.contexto.inicio_estado = time.time()

        self.estado.entrar()


    def tempo_estado(self):

        return time.time() - self.contexto.inicio_estado

    def telemetria_linha(self):
        """Mostra o que o robô está fazendo sem poluir o terminal a cada frame."""
        agora = time.monotonic()
        if agora - self._ultimo_status < setup.TELEMETRIA_INTERVALO_S:
            return
        self._ultimo_status = agora
        self.log(self.robo.status_linha())


    def log(self, texto):

        if self.contexto.debug:

            print(f"[{self.estado.ID.name}] {texto}")


class Start(Estado):

    ID = EstadoID.START

    def entrar(self):
        self.planner.log("Inicializando\n Pode apertar o botão")

    def executar(self):
        if self.robo.botao_pressionado:
            self.planner.log("Botão apertado com sucesso")
            self.planner.mudar_estado(SeguirLinha)


class SeguirLinha(Estado):

    ID = EstadoID.SEGUIR_LINHA

    def entrar(self):

        self.planner.log("Seguindo linha")

    
    def executar(self):

        self.robo.seguir_linha()
        self.planner.telemetria_linha()

        evento = self.robo.evento()

        '''
        if evento == Evento.PRATA:

            self.planner.mudar_estado(EntrarResgate)
            return

        if evento == Evento.VERMELHO:
            self.planner.mudar_estado(Stop)
            return

        if evento == Evento.OBSTACULO:

            self.planner.mudar_estado(Desviar)
            return
        '''
        if evento == Evento.INTERSECAO:

            self.planner.mudar_estado(Intersecao)
            return

        if evento == Evento.LINHA_PERDIDA and not self.robo.recuperar_linha():
            self.planner.log("Linha não recuperada dentro do limite")
            self.planner.mudar_estado(Stop)


class Desviar(Estado):

    ID = EstadoID.DESVIAR

    def entrar(self):

        self.planner.log("Desviando")
        self.desvio = DesvioInteligente(self.robo)


    def executar(self):

        self.desvio.atualizar()
        if self.desvio.concluido:
            self.planner.log("Linha recuperada")
            self.planner.mudar_estado(SeguirLinha)
        elif self.desvio.falhou:
            self.planner.log("Desvio falhou; parado por segurança")
            self.planner.mudar_estado(Stop)


class Intersecao(Estado):

    ID = EstadoID.INTERSECAO

    def entrar(self):

        self.planner.log("Interseção")
        curva = self.robo.curva_detectada()
        graus = -90 if curva == Curva.ESQUERDA else 90 if curva == Curva.DIREITA else 180 if curva == Curva.RETORNO else 0
        self.robo.iniciar_girar(graus)


    def executar(self):

        if self.robo.atualizar_movimento():
            self.planner.mudar_estado(SeguirLinha)


class EntrarResgate(Estado):

    ID = EstadoID.ENTRAR_RESGATE

    def entrar(self):

        self.planner.log("Entrando na sala de resgate")

        self.robo.entrar_resgate()
        self.fase = "alinhar_prata"
        self.movimento_iniciado = False


    def executar(self):

        if self.fase == "alinhar_prata":
            if self.robo.alinhar_faixa_prata():
                self.fase = "cruzar_prata"
            elif self.planner.tempo_estado() > setup.TEMPO_MAX_ENTRADA_RESGATE_S:
                self.planner.log("Faixa prata não alinhada; seguindo com segurança")
                self.fase = "cruzar_prata"
            return

        if self.fase == "cruzar_prata":
            self.robo.frente(setup.VEL_RESGATE)
            if not self.robo.tem_prata():
                self.robo.parar()
                self.fase = "avancar_para_dentro"
            return

        if self.fase == "avancar_para_dentro":
            if not self.movimento_iniciado:
                self.robo.iniciar_andar(setup.AVANCO_ENTRADA_RESGATE_MM, setup.VEL_RESGATE)
                self.movimento_iniciado = True
            elif self.robo.atualizar_movimento():
                self.planner.mudar_estado(Resgate)


class Resgate(Estado):

    ID = EstadoID.RESGATE

    def entrar(self):

        self.planner.log("Modo Resgate")


    def executar(self):

        self.robo.executar_resgate()

        if self.robo.resgate_finalizado():

            self.planner.mudar_estado(SairResgate)

class SairResgate(Estado):

    ID = EstadoID.SAIR_RESGATE

    def entrar(self):

        self.planner.log("Procurando linha de saída")
        self.fase = "buscar"
        self.theta_inicio_busca = self.robo.theta
        self.tentativas = 0


    def executar(self):

        if self.fase == "buscar":
            if self.robo.tem_saida_resgate():
                self.robo.parar()
                self.fase = "aproximar"
                return

            if abs(self.robo.theta - self.theta_inicio_busca) >= 2 * math.pi:
                self.robo.parar()
                self.tentativas += 1
                if self.tentativas > setup.TENTATIVAS_BUSCA_SAIDA:
                    self.planner.log("Saída não localizada; parando por segurança")
                    self.planner.mudar_estado(Stop)
                    return
                self.robo.andar(setup.AVANCO_BUSCA_SAIDA_MM, setup.VEL_RESGATE)
                self.theta_inicio_busca = self.robo.theta
                return

            self.robo.girar_direita(setup.VEL_RESGATE)
            return

        if self.fase == "aproximar":
            if not self.robo.tem_saida_resgate():
                self.fase = "buscar"
                self.theta_inicio_busca = self.robo.theta
                return
            if not self.robo.centralizar_saida_resgate():
                return
            if self.robo.saida_proxima():
                self.robo.parar()
                self.robo.girar(90)
                self.fase = "testar_direita"
            else:
                self.robo.frente(setup.VEL_RESGATE)
            return

        if self.fase == "testar_direita":
            self.robo.andar(setup.AVANCO_TESTE_SAIDA_MM, setup.VEL_RESGATE)
            if self.robo.tem_linha():
                self.robo.sair_resgate()
                self.planner.mudar_estado(SeguirLinha)
            else:
                self.robo.girar(180)
                self.fase = "testar_esquerda"
            return

        if self.fase == "testar_esquerda":
            self.robo.andar(setup.AVANCO_TESTE_SAIDA_MM, setup.VEL_RESGATE)
            if self.robo.tem_linha():
                self.robo.sair_resgate()
                self.planner.mudar_estado(SeguirLinha)
            else:
                self.fase = "buscar"
                self.theta_inicio_busca = self.robo.theta


class Stop(Estado):

    ID = EstadoID.STOP

    def entrar(self):
        self.robo.parar()
        self.planner.log("Parado: saída não localizada")

    def executar(self):
        self.robo.parar()
