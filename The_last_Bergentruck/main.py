#main

from robo import Robo
from planner import Planner


robo = Robo()

planner = Planner(robo)

while True:

    planner.update()