"""Controlador PID discreto com tempo de amostragem explícito."""


class PID:
    def __init__(self, kp, ki, kd, output_limits=(None, None), integral_limits=(None, None), min_dt=1e-3):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.output_limits = output_limits
        self.integral_limits = integral_limits
        self.min_dt = min_dt
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.erro_ant = None

    @staticmethod
    def _clamp(value, limits):
        low, high = limits
        if low is not None:
            value = max(low, value)
        if high is not None:
            value = min(high, value)
        return value

    def atualizar(self, erro, dt=None):
        """Amostras sem dt útil não integram nem derivam."""
        valid_dt = dt is not None and dt >= self.min_dt
        derivada = 0.0
        if valid_dt:
            if self.erro_ant is not None:
                derivada = (erro - self.erro_ant) / dt
            integral_candidato = self._clamp(self.integral + erro * dt, self.integral_limits)
        else:
            integral_candidato = self.integral

        sem_integral = self.kp * erro + self.kd * derivada
        candidata = sem_integral + self.ki * integral_candidato
        saida = self._clamp(candidata, self.output_limits)
        saturou_alto = self.output_limits[1] is not None and candidata > self.output_limits[1]
        saturou_baixo = self.output_limits[0] is not None and candidata < self.output_limits[0]
        # Anti-windup: não acumula erro que aumentaria uma saturação já presente.
        if valid_dt and not ((saturou_alto and erro > 0) or (saturou_baixo and erro < 0)):
            self.integral = integral_candidato
            saida = self._clamp(sem_integral + self.ki * self.integral, self.output_limits)
        self.erro_ant = erro
        return saida
