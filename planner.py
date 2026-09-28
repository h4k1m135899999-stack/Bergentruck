"""Small start/follow/stop loop for the Odisseu line follower."""

import time
import setup


class Planner:
    def __init__(self, robo):
        self.robo = robo
        self.started = False
        self.stopped = False
        self.last_status = 0.0
        print("Odisseu pronto. Aperte o botão para iniciar o seguidor de linha.")

    def update(self):
        if self.stopped:
            return
        if not self.robo.atualizar():
            self.robo.parar()
            return
        if not self.started:
            if self.robo.botao_pressionado:
                self.started = True
                print("Seguindo linha.")
            else:
                return
        if not self.robo.seguir_linha():
            print("Linha não recuperada no tempo limite; motores parados.")
            self.started = False
            self.stopped = True
            return
        now = time.monotonic()
        if now - self.last_status >= setup.TELEMETRIA_INTERVALO_S:
            self.last_status = now
            print(self.robo.status_linha())
