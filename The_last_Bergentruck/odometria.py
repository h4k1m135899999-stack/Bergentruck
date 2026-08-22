#odometria

import math


class Odometria:


    def __init__(
        self,
        RAIO_RODA,
        DISTANCIA_RODAS,
        PULSOS_VOLTA
    ):

        self.raio = RAIO_RODA
        self.L = DISTANCIA_RODAS
        self.ppr = PULSOS_VOLTA

        self.reset()

    def reset(self):
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0


        self.ant_L = 0
        self.ant_R = 0



    def atualizar(
        self,
        pulsos_L,
        pulsos_R
    ):

        delta_L = pulsos_L - self.ant_L
        delta_R = pulsos_R - self.ant_R


        self.ant_L = pulsos_L
        self.ant_R = pulsos_R


        dist_L = (
            delta_L / self.ppr
        ) * (2 * math.pi * self.raio)


        dist_R = (
            delta_R / self.ppr
        ) * (2 * math.pi * self.raio)


        deslocamento = (
            dist_L + dist_R
        ) / 2


        rotacao = (
            dist_R - dist_L
        ) / self.L


        # Integra no centro do arco, não na orientação já rotacionada.
        theta_medio = self.theta + rotacao / 2.0
        self.x += deslocamento * math.cos(theta_medio)
        self.y += deslocamento * math.sin(theta_medio)
        self.theta = math.atan2(
            math.sin(self.theta + rotacao), math.cos(self.theta + rotacao)
        )
    


    def pose(self):
        return (
            self.x,
            self.y,
            self.theta
        )
