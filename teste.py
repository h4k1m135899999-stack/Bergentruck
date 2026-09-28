from robo import Robo
from time import sleep
robo = Robo()

def mover(x, y, z = 0):
    robo.set_motores(x, y)
    sleep(z)

def parar(z):
    mover(0,0)
    sleep(z)

def girar(grau):
    if grau == 0:
        mover(0.2, -0.2, 0.6)
    if grau == 1:
        mover(-0.2, 0.2, 0.6)
while True:
    #robo.girar(90)
    #robo.andar(2)

    #robo.girar(90)

    mover(-0.2, 0.2, 0.6)
    parar(1)

    #robo.tras(0.3)
