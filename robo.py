"""Hardware interface and line-following controller for Odisseu."""

import time

import setup
from encoder import Encoder
from odometria import Odometria
from pid import PID
from vision import Vision


class Robo:
    def __init__(self):
        self.botao = setup.botao
        self.motorL, self.motorR = setup.motorL, setup.motorR
        self.encoderL = Encoder(setup.encoderL_a, setup.encoderL_b)
        self.encoderR = Encoder(setup.encoderR_a, setup.encoderR_b)
        self.odom = Odometria(setup.RAIO_RODA, setup.DISTANCIA_RODAS, setup.PULSOS_VOLTA)
        self.vision = Vision()
        self._pid_encoder = PID(setup.KP_E, setup.KI_E, setup.KD_E,
                                output_limits=(-0.35, 0.35), integral_limits=(-50, 50))
        self._pid_linha = PID(setup.KP_L, setup.KI_L, setup.KD_L,
                              output_limits=(-0.45, 0.45), integral_limits=(-2, 2))
        self._last_control = time.monotonic()
        self._last_encoder_control = time.monotonic()
        self._encoder_left_previous = self.encoderL.ler()
        self._encoder_right_previous = self.encoderR.ler()
        self._last_error = 0.0
        self._filtered_error = None
        self._lost_frames = 0
        self._lost_since = None
        self._command = (0.0, 0.0)
        self.botao_pressionado = False
        self._fps = 0.0

    def iniciar(self):
        if self.botao is None:
            raise RuntimeError("Botão GPIO indisponível; verifique a instalação no robô.")
        self.botao.when_pressed = self._botao_pressionado

    def _botao_pressionado(self):
        self.botao_pressionado = True

    def atualizar(self):
        start = time.perf_counter()
        self.odom.atualizar(self.encoderL.ler(), self.encoderR.ler())
        if not self.vision.update():
            return False
        elapsed = time.perf_counter() - start
        if elapsed > 0:
            inst = 1.0 / elapsed
            self._fps = inst if not self._fps else 0.85 * self._fps + 0.15 * inst
        if self.tem_linha():
            if self._lost_frames:
                self._pid_linha.reset()
                self._filtered_error = None
            self._last_error = self.vision.center_error
            self._lost_frames = 0
            self._lost_since = None
        else:
            self._lost_frames += 1
        return True

    def tem_linha(self):
        return self.vision.line_found

    @property
    def erro_linha(self):
        return self.vision.center_error if self.tem_linha() else self._last_error

    @property
    def heading(self):
        return self.vision.heading

    def set_motores(self, velL, velR):
        velL = max(-1.0, min(1.0, float(velL)))
        velR = max(-1.0, min(1.0, float(velR)))
        self._command = (velL, velR)
        (self.motorL.forward if velL >= 0 else self.motorL.backward)(abs(velL))
        (self.motorR.forward if velR >= 0 else self.motorR.backward)(abs(velR))

    def parar(self):
        self._command = (0.0, 0.0)
        self.motorL.stop()
        self.motorR.stop()

    def seguir_linha(self, vel=setup.VEL_MED):
        if not self.tem_linha():
            if self._lost_since is None:
                self._lost_since = time.monotonic()
            # Em curvas fechadas, inicia a busca imediatamente na direção do
            # último erro; em pequenas falhas mantém avanço reduzido por poucos frames.
            if abs(self._last_error) >= setup.ERRO_PERDIDA_GIRA or self._lost_frames >= setup.LINHA_FRAMES_RECUPERAR:
                return self.recuperar_linha()
            vel *= 0.7 if self._lost_frames < setup.LINHA_FRAMES_REDUZIR else 0.45

        error = self.erro_linha * setup.PESO_ERRO_POS + self.heading * setup.PESO_LOOKAHEAD
        if self._filtered_error is None:
            self._filtered_error = error
        else:
            self._filtered_error += setup.FILTRO_ERRO_ALFA * (error - self._filtered_error)

        now = time.monotonic()
        dt = max(0.005, now - self._last_control)
        self._last_control = now
        correction = self._pid_linha.atualizar(self._filtered_error, dt)
        correction = max(-setup.GIRO_MAX_FRAC * vel, min(setup.GIRO_MAX_FRAC * vel, correction))
        curve_brake = 1.0 - setup.FRENO_CURVA_FRAC * min(1.0, abs(self._filtered_error))
        base = vel * curve_brake
        base_left, base_right = self._encoder_trim(base)
        # Permite a roda interna desacelerar e até inverter em curvas agudas.
        floor = -setup.GIRO_REVERSO_MAX_FRAC * vel
        left = max(floor, min(1.0, base_left + setup.SENTIDO_CORRECAO * correction))
        right = max(floor, min(1.0, base_right - setup.SENTIDO_CORRECAO * correction))
        self.set_motores(left, right)
        return True

    def _encoder_trim(self, base):
        now = time.monotonic()
        dt = now - self._last_encoder_control
        self._last_encoder_control = now
        left_count = self.encoderL.ler()
        right_count = self.encoderR.ler()
        left_delta = left_count - self._encoder_left_previous
        right_delta = right_count - self._encoder_right_previous
        self._encoder_left_previous = left_count
        self._encoder_right_previous = right_count
        speed_error = (left_delta - right_delta) / dt if dt > 0 else 0.0
        trim = self._pid_encoder.atualizar(speed_error, dt)
        trim = max(-setup.TRIM_ENCODER_MAX, min(setup.TRIM_ENCODER_MAX, trim))
        return max(0.0, base - trim), max(0.0, base + trim)

    def recuperar_linha(self):
        if self._lost_since is None:
            self._lost_since = time.monotonic()
        if time.monotonic() - self._lost_since > setup.TEMPO_MAX_RECUPERAR_LINHA_S:
            self.parar()
            return False
        side = 1 if self._last_error >= 0 else -1
        self.set_motores(0.16 * side, -0.16 * side)
        return True

    def status_linha(self):
        if not self.tem_linha() or self.vision.center_error is None:
            reading = "linha não encontrada; buscando"
        else:
            error = self.vision.center_error
            side = "no centro" if abs(error) < 0.05 else ("à direita" if error > 0 else "à esquerda")
            reading = f"linha {side} ({abs(error) * 100:.0f}% da largura)"
        left, right = self._command
        return f"Odisseu seguindo linha: {reading}. motores E={left:+.2f}, D={right:+.2f}. fps={self.vision.fps:.1f}."

    def release(self):
        self.parar()
        self.vision.release()
