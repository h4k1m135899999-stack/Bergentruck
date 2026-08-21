"""Desvio visual, suave e não bloqueante de obstáculos."""

import time

import setup


class DesvioInteligente:
    """Recupera a linha usando as saídas visíveis ao redor do obstáculo."""

    def __init__(self, robo):
        self.robo = robo
        self.fase = "analisar"
        self.lado = None
        self.inicio = time.monotonic()
        self.origem = (robo.x, robo.y)
        self.concluido = False
        self.falhou = False

    def atualizar(self):
        if self.concluido or self.falhou:
            return

        if time.monotonic() - self.inicio > setup.TEMPO_MAX_DESVIO_S:
            self.robo.parar()
            self.falhou = True
            return

        if self.fase == "analisar":
            lado_linha = self.robo.lado_linha_obstaculo()
            if lado_linha is None:
                return
            self.lado = lado_linha
            self.lado_contorno = (
                lado_linha
                if lado_linha in ("esquerda", "direita")
                else self.robo.lado_livre_obstaculo()
            )
            self.fase = "alinhar_borda"
            return

        if self.fase == "alinhar_borda":
            if self.robo.alinhar_borda_obstaculo(self.lado_contorno):
                self.origem = (self.robo.x, self.robo.y)
                self.fase = "sair_da_linha" if self.lado != "atras" else "perder_obstaculo"
            return

        if self.fase == "sair_da_linha":
            self.robo.frente(setup.VEL_DESVIO)
            if self._percorreu(setup.AVANCO_SAIDA_LINHA_MM):
                self.origem = (self.robo.x, self.robo.y)
                self.fase = "procurar_linha"
            return

        if self.fase == "procurar_linha":
            self.robo.curva_suave(self.lado, setup.VEL_DESVIO)
            if self.robo.linha_perto():
                self.fase = "alinhar_linha"
            elif self._percorreu(setup.AVANCO_MAX_DESVIO_MM):
                self.falhou = True
                self.robo.parar()
            return

        if self.fase == "perder_obstaculo":
            self.robo.curva_suave(self.lado_contorno, setup.VEL_DESVIO)
            if not self.robo.tem_obstaculo():
                self.fase = "reencontrar_obstaculo"
            elif self._percorreu(setup.AVANCO_MAX_DESVIO_MM):
                self.falhou = True
                self.robo.parar()
            return

        if self.fase == "reencontrar_obstaculo":
            self.robo.girar_para_lado(self._oposto(self.lado_contorno), setup.VEL_DESVIO)
            if self.robo.tem_obstaculo() and self.robo.alinhar_borda_obstaculo(self.lado_contorno):
                self.origem = (self.robo.x, self.robo.y)
                self.fase = "voltar_para_linha"
            return

        if self.fase == "voltar_para_linha":
            self.robo.curva_suave(self._oposto(self.lado_contorno), setup.VEL_DESVIO)
            if self.robo.linha_perto():
                self.fase = "alinhar_linha"
            elif self._percorreu(setup.AVANCO_MAX_DESVIO_MM):
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
