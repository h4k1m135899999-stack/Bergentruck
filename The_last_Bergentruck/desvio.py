"""Desvio visual, suave e não bloqueante de obstáculos."""

import time

import setup


class DesvioInteligente:
    """Recupera a linha usando as saídas visíveis ao redor do obstáculo."""

    def __init__(self, robo):
        self.robo = robo
        self.fase = "escolher_lado"
        self.lado = None
        self.inicio = time.monotonic()
        self.origem = (robo.x, robo.y)
        self.obstaculo_sumiu_frames = 0
        self.linha_frames = 0
        self.concluido = False
        self.falhou = False

    def atualizar(self):
        # Disponível para telemetria/debug sem duplicar decisão no Planner.
        self.robo.memoria["estado_desvio"] = self.fase
        if self.concluido or self.falhou:
            return

        if time.monotonic() - self.inicio > setup.TEMPO_MAX_DESVIO_S:
            self.robo.parar()
            self.falhou = True
            return

        if self.fase == "escolher_lado":
            lado_linha = self.robo.lado_linha_obstaculo()
            # Escolha única: evidência da linha vence; empate é determinístico.
            self.lado = lado_linha if lado_linha in ("esquerda", "direita") else self.robo.lado_livre_obstaculo()
            self.origem = (self.robo.x, self.robo.y)
            self.fase = "sair_da_frente"
            return

        if self.fase == "sair_da_frente":
            self.robo.curva_suave(self.lado, setup.VEL_DESVIO)
            if self._percorreu(setup.DESVIO_LATERAL_MM):
                self.origem = (self.robo.x, self.robo.y)
                self.fase = "contornar"
            return

        if self.fase == "contornar":
            self.robo.frente(setup.VEL_DESVIO)
            self.obstaculo_sumiu_frames = self.obstaculo_sumiu_frames + 1 if not self.robo.tem_obstaculo() else 0
            # Não basta ver a linha: ela pode estar atrás do objeto (foto de teste).
            if (self._percorreu(setup.DESVIO_AVANCO_MM)
                    and self.obstaculo_sumiu_frames >= setup.OBSTACULO_FRAMES_SAIDA):
                self.origem = (self.robo.x, self.robo.y)
                self.fase = "procurar_linha"
            return

        if self.fase == "procurar_linha":
            self.robo.curva_suave(self._oposto(self.lado), setup.VEL_DESVIO)
            self.linha_frames = self.linha_frames + 1 if self.robo.tem_linha() else 0
            if self.linha_frames >= setup.LINHA_FRAMES_CONFIRMACAO:
                self.fase = "alinhar_linha"
            elif self._percorreu(setup.DESVIO_RETORNO_MM):
                self.falhou = True
                self.robo.parar()
            return

        if self.fase == "alinhar_linha" and self.robo.alinhar_linha(setup.VEL_DESVIO):
            self.concluido = True

    def _percorreu(self, limite_mm):
        return self.robo.distancia_desde(self.origem) >= limite_mm

    @staticmethod
    def _oposto(lado):
        return "direita" if lado == "esquerda" else "esquerda"
