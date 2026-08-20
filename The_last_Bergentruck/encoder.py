#encoder

import lgpio


class Encoder:


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