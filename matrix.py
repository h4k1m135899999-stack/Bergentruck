from robo import Robo
from time import sleep
import time

robo = Robo()

def mover(x, y, tempo = 0):
    robo.set_motores(x, y)
    sleep(tempo)
def mover(x, y, tempo = 0):
    robo.set_motores(x, y)
    sleep(tempo)

def parar(tempo):
    mover(0,0)
    sleep(tempo)

def girar(grau):
    if grau == 0:
        mover(0.2, -0.2, 0.6)
    if grau == 1:
        mover(-0.2, 0.2, 0.6)

def seguir_linha_mod(tempo = 4):
    agora = time.monotonic()

    while time.monotonic() - agora < tempo:
        robo.atualizar()
        robo.seguir_linha()
        
def primeiro_seguir_linha(tempo=4):
    agora = time.monotonic()

    while time.monotonic() - agora < tempo:
        robo.atualizar()

        if not robo.tem_linha():
            break

        robo.seguir_linha()

#Que comassem os jogos
mover(0.4,0.4, 1)
girar(1)
parar(0.5)
primeiro_seguir_linha(7)
girar(1)
mover(0.2, 0.2, 0.6)
girar(0)
