#encoder

import lgpio


class Encoder:

    """Decodificação x1: subida em A e leitura de B para direção.

    PULSOS_VOLTA deve corresponder exatamente a este modo. Quadrature x4 só
    deve ser habilitado após confirmar os dois canais, níveis lógicos e carga
    de interrupções no Raspberry; mudar para x4 exige multiplicar a escala.
    """


    def __init__(self, gpio_a, gpio_b):

        self.contador = 0

        self.a = gpio_a
        self.b = gpio_b


        self.h = lgpio.gpiochip_open(0)


        lgpio.gpio_claim_input(
            self.h,
            self.a
        )

        lgpio.gpio_claim_input(
            self.h,
            self.b
        )


        lgpio.callback(
            self.h,
            self.a,
            lgpio.RISING_EDGE,
            self.callback
        )



    def callback(
        self,
        chip,
        gpio,
        level,
        tick
    ):

        if lgpio.gpio_read(
            self.h,
            self.b
        ):

            self.contador += 1

        else:

            self.contador -= 1



    def ler(self):

        return self.contador
    def reset(self):
        self.contador = 0
