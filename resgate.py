"""Maquina de estados exclusiva da sala de resgate."""

from enum import Enum, auto


class EstadoResgate(Enum):
    PROCURAR_VITIMA = auto()
    ALINHAR_VITIMA = auto()
    APROXIMAR = auto()
    CAPTURAR = auto()
    PROCURAR_AREA_VIVAS = auto()
    APROXIMAR_AREA_VIVAS = auto()
    ENTREGAR_VIVAS = auto()
    PROCURAR_AREA_MORTA = auto()
    APROXIMAR_AREA_MORTA = auto()
    ENTREGAR_MORTA = auto()
    PROCURAR_SAIDA = auto()
    FINALIZADO = auto()


class ControladorResgate:
    """Coordena resgate usando apenas a API publica de :class:`Robo`."""

    def __init__(self, robo):
        self.robo = robo
        self.estado = EstadoResgate.PROCURAR_VITIMA
        self.vitimas_vivas_capturadas = 0
        self.vitima_morta_capturada = False
        self.ultima_vitima = None
        self.acoes = {
            EstadoResgate.PROCURAR_VITIMA: self._procurar_vitima,
            EstadoResgate.ALINHAR_VITIMA: self._alinhar_vitima,
            EstadoResgate.APROXIMAR: self._aproximar_vitima,
            EstadoResgate.CAPTURAR: self._capturar_vitima,
            EstadoResgate.PROCURAR_AREA_VIVAS: self._procurar_area_vivas,
            EstadoResgate.APROXIMAR_AREA_VIVAS: self._aproximar_area_vivas,
            EstadoResgate.ENTREGAR_VIVAS: self._entregar_vivas,
            EstadoResgate.PROCURAR_AREA_MORTA: self._procurar_area_morta,
            EstadoResgate.APROXIMAR_AREA_MORTA: self._aproximar_area_morta,
            EstadoResgate.ENTREGAR_MORTA: self._entregar_morta,
            EstadoResgate.PROCURAR_SAIDA: self._procurar_saida,
        }

    def atualizar_observacao(self):
        if self.robo.tem_vitima():
            self.ultima_vitima = self.robo.tipo_vitima()

    def executar(self):

        self.atualizar_observacao()

        acao = self.acoes.get(self.estado)

        if acao is not None:
            acao()

    def _procurar_vitima(self):
        self.robo.girar_direita(0.20)
        if self.robo.tem_vitima():
            self.robo.parar()
            self.estado = EstadoResgate.ALINHAR_VITIMA

    def _alinhar_vitima(self):
        if not self.robo.tem_vitima():
            self.estado = EstadoResgate.PROCURAR_VITIMA
        elif self.robo.centralizar_vitima():
            self.estado = EstadoResgate.APROXIMAR

    def _aproximar_vitima(self):
        if not self.robo.tem_vitima():
            self.estado = EstadoResgate.PROCURAR_VITIMA
            return

        if not self.robo.centralizar_vitima():
            return

        distancia = self.robo.distancia_vitima()
        if distancia is None:
            return

        if distancia <= self.robo.distancia_captura_mm:
            self.robo.parar()
            self.estado = EstadoResgate.CAPTURAR
        else:
            self.robo.frente(0.18)

    def _capturar_vitima(self):
        # Salva o tipo antes de movimentar a garra, quando a bola ainda aparece.
        tipo = self.robo.tipo_vitima() or self.ultima_vitima
        if tipo is None:
            self.estado = EstadoResgate.PROCURAR_VITIMA
            return

        self.robo.capturar_vitima()

        if tipo == "silver":
            self.vitimas_vivas_capturadas += 1
        elif tipo == "dark":
            self.vitima_morta_capturada = True

        if self.vitimas_vivas_capturadas >= 2:
            self.estado = EstadoResgate.PROCURAR_AREA_VIVAS
        elif self.vitima_morta_capturada:
            self.estado = EstadoResgate.PROCURAR_AREA_MORTA
        else:
            self.estado = EstadoResgate.PROCURAR_VITIMA

    def _procurar_area_vivas(self):
        self._procurar_area("verde", EstadoResgate.APROXIMAR_AREA_VIVAS)

    def _aproximar_area_vivas(self):
        self._aproximar_area("verde", EstadoResgate.PROCURAR_AREA_VIVAS,
                              EstadoResgate.ENTREGAR_VIVAS)

    def _entregar_vivas(self):
        self.robo.entregar_vitima()
        self.vitimas_vivas_capturadas = 0
        self.estado = (
            EstadoResgate.PROCURAR_AREA_MORTA
            if self.vitima_morta_capturada
            else EstadoResgate.PROCURAR_VITIMA
        )

    def _procurar_area_morta(self):
        self._procurar_area("vermelha", EstadoResgate.APROXIMAR_AREA_MORTA)

    def _aproximar_area_morta(self):
        self._aproximar_area("vermelha", EstadoResgate.PROCURAR_AREA_MORTA,
                              EstadoResgate.ENTREGAR_MORTA)

    def _entregar_morta(self):
        self.robo.entregar_vitima()
        self.vitima_morta_capturada = False
        self.estado = EstadoResgate.PROCURAR_SAIDA

    def _procurar_area(self, cor, proximo_estado):
        self.robo.girar_direita(0.18)
        if self.robo.tem_area_entrega(cor):
            self.robo.parar()
            self.estado = proximo_estado

    def _aproximar_area(self, cor, estado_busca, estado_entrega):
        if not self.robo.tem_area_entrega(cor):
            self.estado = estado_busca
            return

        if not self.robo.centralizar_area_entrega(cor):
            return

        if self.robo.area_entrega_proxima(cor):
            self.robo.parar()
            self.estado = estado_entrega
        else:
            self.robo.frente(0.18)

    def _procurar_saida(self):
        self.robo.girar_direita(0.2)
        if self.robo.tem_saida_resgate():
            self.robo.parar()
            self.estado = EstadoResgate.FINALIZADO

    @property
    def finalizado(self):
        return self.estado == EstadoResgate.FINALIZADO
