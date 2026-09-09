from setup import servo_claw, servo_lift, servo_dump
import keyboard
from time import sleep

print("Controle dos servos iniciado!")
print("A/D = Garra")
print("W/S = Lift")
print("Q/E = Dump")
print("ESC = Sair")

while True:

    # Garra
    if keyboard.is_pressed('a'):
        servo_claw.min()
        print("Garra: mínimo")
        sleep(0.2)

    if keyboard.is_pressed('d'):
        servo_claw.max()
        print("Garra: máximo")
        sleep(0.2)

    # Lift
    if keyboard.is_pressed('w'):
        servo_lift.max()
        print("Lift: máximo")
        sleep(0.2)

    if keyboard.is_pressed('s'):
        servo_lift.min()
        print("Lift: mínimo")
        sleep(0.2)

    # Dump
    if keyboard.is_pressed('q'):
        servo_dump.min()
        print("Dump: mínimo")
        sleep(0.2)

    if keyboard.is_pressed('e'):
        servo_dump.max()
        print("Dump: máximo")
        sleep(0.2)

    # Sair
    if keyboard.is_pressed('esc'):
        print("Encerrando...")
        break

    sleep(0.05)
