#from abc import executar_captura
from setup import servo_claw, servo_lift, servo_dump
from time import sleep

#executar_captura()

servo_claw.min()
sleep(0.5)

servo_claw.max()
sleep(0.5)

servo_lift.min()
sleep(0.5)

servo_lift.max()
sleep(0.5)

servo_dump.min()
sleep(0.5)

servo_dump.max()
sleep(0.5)

#servo_claw.min() #Braço inteiro
#servo_lift.max()
#servo_dump.max()