# Odisseu

Seguidor de linha para Raspberry Pi. O `main.py` inicia a câmera e os motores;
pressione o botão conectado ao GPIO 2 para começar. `enviar.cmd` mantém o atalho
de envio e encaminha a mensagem opcional para `enviar.ps1`.

## Ajuste de câmera e curvas

Os parâmetros ficam em `setup.py`: resolução, FPS solicitado, velocidade e
ganhos do controlador. A câmera pode ignorar o FPS solicitado; o valor impresso
na telemetria mede a taxa real do ciclo de captura e processamento.

Se o robô corrigir para o lado errado, inverta `SENTIDO_CORRECAO`. Se cortar
curvas por fora, ajuste `KP_L`, `PESO_LOOKAHEAD` ou `GIRO_MAX_FRAC` com o robô
em um local seguro. O controle permite reduzir e inverter a roda interna para
fazer curvas fechadas.
