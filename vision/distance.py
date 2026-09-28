"""Estimativa de distancia por tamanho aparente da bola na imagem."""


class EstimadorDistanciaCamera:
    """Usa o modelo pinhole: distancia = diametro_real * focal / diametro_px.

    A distancia focal deve ser calibrada para a resolucao configurada na camera.
    """

    def __init__(self, diametro_bola_mm, distancia_focal_px):
        self.diametro_bola_mm = diametro_bola_mm
        self.distancia_focal_px = distancia_focal_px

    def estimar_bola_mm(self, diametro_px):
        if diametro_px is None or diametro_px <= 0:
            return None

        return (
            self.diametro_bola_mm
            * self.distancia_focal_px
            / diametro_px
        )
