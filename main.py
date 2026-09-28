#main

from robo import Robo
from planner import Planner

robo = Robo()
try:
    robo.iniciar()
    planner = Planner(robo)
    while True:
        planner.update()
except KeyboardInterrupt:
    print("Encerrando Odisseu.")
finally:
    robo.release()
