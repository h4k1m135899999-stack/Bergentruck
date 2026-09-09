#from abc import executar_captura
from setup import servo_claw, servo_lift, servo_dump

#executar_captura()

while True:
    servo_claw.max() #Braço inteiro
    servo_claw.min()
    servo_claw.mid()

#servo_lift.mid()
#servo_dump.max()