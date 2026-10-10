from gpiozero import Motor

left = Motor(forward=10, backward=9, enable=11)
right = Motor(forward=27, backward=22, enable=17)

while True:
    left.forward
    right.forward