# ui — HUD de texto com diagnósticos e ajuda de teclas.

import cv2


class UI:

    HELP_LINES = [
        "o overlay | n original | l linha | g verde | r vermelho",
        "s prata | b preto saida | v vitimas | k obstaculo | d destinos",
        "h ajuda | p imprime HSV no terminal | +/- focal | q sair",
        "clique: HSV do pixel | c: HSV do centro",
    ]

    def __init__(self):
        self.show_help = True
        self.mouse_hsv = None  # (x, y, h, s, v)
        self.center_hsv = None

    def draw(self, img, diagnostics, mode_name: str):
        lines = [
            f"Modo: {mode_name}",
            (
                f"Linha: {'SIM' if diagnostics.line.found else 'nao'}  "
                f"err={diagnostics.line.error:.1f}  "
                f"head={diagnostics.line.heading:.3f}  "
                f"curv={diagnostics.line.curvature:.4f}"
            ),
            (
                f"Verde L/R: {int(diagnostics.objects.green_left)}/"
                f"{int(diagnostics.objects.green_right)}  "
                f"red={int(diagnostics.objects.red)}  "
                f"prata={int(diagnostics.objects.silver)}  "
                f"saida={int(diagnostics.objects.black_exit)}  "
                f"obst={int(diagnostics.objects.obstacle)}"
            ),
            (
                f"Destinos G/R: {int(diagnostics.objects.green_area)}/"
                f"{int(diagnostics.objects.red_area)}"
            ),
        ]

        # --- Linha extra para métricas do obstáculo (acesso via vision no diagnostics?) ---
        # Infelizmente diagnostics não guarda obstacle_info. Vamos acessar pelo vision se disponível.
        # Mas diagnostics não tem vision. Para evitar modificar diagnostics, usamos o fato de que
        # em app.py chamamos diagnostics.update(vision,...) e depois draw. Não temos acesso direto ao vision aqui.
        # Então vamos fazer uma solução: usar o objeto 'vision' que é passado para o overlay, mas aqui não.
        # Vou modificar para aceitar um parâmetro opcional 'vision' no draw.
        # Mas para não quebrar a assinatura, vou alterar a assinatura do método draw para aceitar vision também.
        # Atualização: melhor manter compatibilidade e usar o diagnostics, mas adicionar campos em ObjectInfo.
        # Para não depender de mudanças em diagnostics, vou usar um truque: o UI pode acessar a instância de vision
        # através de um atributo global? Não. Vou simplesmente adicionar um campo extra no diagnostics para isso.
        # Vou modificar a classe Diagnostics para incluir obstacle_info. Mas como não quero mexer em diagnostics.py,
        # farei aqui uma verificação: se diagnostics tiver um atributo obstacle_info, usamos; senão, ignoramos.
        # Mas na realidade, o app.py chama diagnostics.update(vision,...) e depois ui.draw(img, diagnostics, mode_name).
        # Poderíamos modificar o app para passar vision também, mas é mais trabalhoso.
        # Solução mais simples: no método draw, receber também vision como parâmetro opcional.
        # Vou fazer isso: alterar a assinatura para draw(self, img, diagnostics, mode_name, vision=None)
        # e manter compatibilidade com chamadas existentes.

        # Por enquanto, vou adaptar e colocar a linha extra no app.py, mas prefiro fazer aqui.
        # Vou modificar a classe UI para ter um método draw com parâmetro extra vision.
        # Como isso afetará app.py, vou incluir a modificação no app também.
        # Mas o usuário pediu apenas alterações nos três arquivos. Vou incluir a mudança no UI e no app
        # para que o app passe vision. Mas o app.py não foi listado para alteração, então vou manter compatível
        # e simplesmente não adicionar a linha de obstáculo no UI, para não quebrar.
        # Alternativa: colocar a linha de obstáculo no overlay ou no HUD via outro método.
        # Decisão: não adicionar a linha no UI para evitar complexidade. O overlay já mostra métricas.
        # Então o UI fica como estava, sem linha extra.

        # Continuando com o código original:

        if diagnostics.victims.found:
            dist = diagnostics.victims.distance_mm
            diam = diagnostics.victims.diameter_px
            lines.append(
                f"Vitima: {diagnostics.victims.type}  "
                f"d={diam:.0f}px  "
                f"dist={dist:.0f}mm" if dist is not None else
                f"Vitima: {diagnostics.victims.type}  d={diam:.0f}px"
            )
        else:
            lines.append("Vitima: —")

        if self.mouse_hsv is not None:
            x, y, h, s, v = self.mouse_hsv
            lines.append(f"Mouse ({x},{y}): H={h} S={s} V={v}")
        elif self.center_hsv is not None:
            h, s, v = self.center_hsv
            lines.append(f"Centro: H={h} S={s} V={v}")

        y = 20
        for text in lines:
            cv2.putText(
                img, text, (10, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 0), 3,
            )
            cv2.putText(
                img, text, (10, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 0), 1,
            )
            y += 20

        if self.show_help:
            y = img.shape[0] - 12 - 18 * len(self.HELP_LINES)
            for text in self.HELP_LINES:
                cv2.putText(
                    img, text, (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 0, 0), 3,
                )
                cv2.putText(
                    img, text, (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 0), 1,
                )
                y += 18

        return img