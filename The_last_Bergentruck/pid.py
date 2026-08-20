#pid

class PID:

    def __init__(self, kp, ki, kd):

        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.integral = 0
        self.erro_ant = 0


    def reset(self):

        self.integral = 0
        self.erro_ant = 0


    def atualizar(self, erro):

        self.integral += erro

        derivada = erro - self.erro_ant

        self.erro_ant = erro

        return (
            self.kp*erro
            +
            self.ki*self.integral
            +
            self.kd*derivada
        )