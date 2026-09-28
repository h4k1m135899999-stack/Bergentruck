#main

from robo import Robo
from planner import Planner

robo = Robo()
robo.iniciar()

planner = Planner(robo)

while True:

    planner.update()