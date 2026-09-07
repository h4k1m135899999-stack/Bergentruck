from robo import Robo
from time import sleep

robo = Robo()

def mover(x, y, z = 0):
    robo.set_motores(x, y)
    sleep(z)

while True:
    robo.atualizar()
    robo.seguir_linha()