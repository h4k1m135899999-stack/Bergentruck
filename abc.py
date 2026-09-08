from robo import Robo
from time import sleep
import time
import math
import setup
robo = Robo()

# Constantes de tempo (ajuste conforme necessário)
TEMPO_GIRO_ESQUERDA = 0.6    # tempo para girar ~90° (ajustar)
TEMPO_MEIA_VOLTA = 1.2       # tempo para meia volta ~180° (ajustar)
TEMPO_ALINHAR_LINHA = 3.0    # tempo máximo para alinhar com a linha
TEMPO_SEGUIR_LINHA = 8.0     # tempo máximo seguindo linha
TEMPO_CAPTURA = 2.0          # tempo para executar captura
TEMPO_DESPEJO = 2.0          # tempo para executar despejo

def mover(x, y, tempo=0):
    """Move os motores com velocidades x (esquerdo) e y (direito)"""
    robo.set_motores(x, y)
    if tempo > 0:
        sleep(tempo)

def parar(tempo=0):
    """Para o robô"""
    mover(0, 0)
    if tempo > 0:
        sleep(tempo)

def girar(grau, tempo=0.6):
    """
    Gira o robô:
    - grau = 0: gira para a direita
    - grau = 1: gira para a esquerda
    """
    if grau == 0:  # Direita
        mover(0.2, -0.2, tempo)
    elif grau == 1:  # Esquerda
        mover(-0.2, 0.2, tempo)

def girar_ate_linha(direcao=1, tempo_max=3.0):
    """
    Gira até encontrar a linha.
    direcao = 1: esquerda, direcao = -1: direita
    Retorna True se encontrou a linha, False se timeout
    """
    inicio = time.monotonic()
    while time.monotonic() - inicio < tempo_max:
        robo.atualizar()
        if robo.tem_linha():
            parar(0.1)
            return True
        if direcao == 1:
            robo.set_motores(-0.15, 0.15)
        else:
            robo.set_motores(0.15, -0.15)
        sleep(0.02)
    parar()
    return False

def alinhar_com_linha(tempo_max=3.0):
    """
    Alinha o robô com a linha usando o heading da visão.
    Retorna True se alinhou, False se timeout
    """
    inicio = time.monotonic()
    while time.monotonic() - inicio < tempo_max:
        robo.atualizar()
        
        if not robo.tem_linha():
            continue
            
        erro = robo.heading  # heading em radianos
        
        if abs(erro) < math.radians(5):  # tolerância de 5°
            parar(0.1)
            return True
            
        if erro > 0:
            robo.set_motores(-0.12, 0.12)  # vira esquerda
        else:
            robo.set_motores(0.12, -0.12)  # vira direita
        sleep(0.02)
    parar()
    return False

def seguir_linha_ate_perder(tempo_max=10.0):
    """
    Segue a linha até perdê-la ou atingir o tempo máximo.
    Retorna True se perdeu a linha, False se timeout
    """
    inicio = time.monotonic()
    
    while time.monotonic() - inicio < tempo_max:
        robo.atualizar()
        
        # Se perdeu a linha
        if not robo.tem_linha():
            parar(0.1)
            return True
            
        robo.seguir_linha()
        sleep(0.02)
    
    parar()
    return False

def meia_volta_e_alinhar(tempo_giro=1.2, tempo_alinhar=3.0):
    """
    Dá meia volta e depois se alinha com a linha.
    Retorna True se conseguiu alinhar, False se não
    """
    # Gira 180° (meia volta)
    girar(1, tempo_giro)  # gira para esquerda por 1.2s (ajustar)
    parar(0.2)
    
    # Procura e alinha com a linha
    if girar_ate_linha(direcao=-1, tempo_max=tempo_alinhar):
        return alinhar_com_linha(tempo_max=tempo_alinhar)
    
    return False

def executar_captura():
    """Executa a sequência de captura da vítima"""
    print("🔄 Iniciando CAPTURA...")
    
    print("✅ Captura finalizada!")

def executar_despejo():
    """Executa a sequência de despejo da vítima"""
    print("🔄 Iniciando DESPEJO...")
    robo.entregar_vitima()
    print("✅ Despejo finalizado!")

def executar_ciclo_completo():
    """
    Executa o ciclo completo:
    1. Anda pra frente
    2. Gira pra esquerda até alinhar com a linha
    3. Segue linha até perder
    4. Meia volta e alinha
    5. Modo CAPTURA
    6. Segue linha até perder
    7. Meia volta e alinha
    8. Modo DESPEJO
    """
    
    print("🚀 Iniciando ciclo completo!")
    
    # ===== PASSO 1: Andar pra frente =====
    print("📌 PASSO 1: Andando pra frente...")
    mover(0.4, 0.4, 1.0)
    parar(0.2)
    
    # ===== PASSO 2: Girar até alinhar com a linha =====
    print("📌 PASSO 2: Girando até alinhar com a linha...")
    if not girar_ate_linha(direcao=1, tempo_max=TEMPO_ALINHAR_LINHA):
        print("⚠️ Não encontrou linha! Tentando direção oposta...")
        girar_ate_linha(direcao=-1, tempo_max=2.0)
    
    # Alinha finamente
    alinhar_com_linha(TEMPO_ALINHAR_LINHA)
    parar(0.2)
    
    # ===== PASSO 3: Seguir linha até perder =====
    print("📌 PASSO 3: Seguindo linha até perder...")
    linha_perdida = seguir_linha_ate_perder(TEMPO_SEGUIR_LINHA)
    if not linha_perdida:
        print("⚠️ Timeout: não perdeu a linha a tempo! Forçando parada...")
    parar(0.3)
    
    # ===== PASSO 4: Meia volta e alinhar =====
    print("📌 PASSO 4: Meia volta e alinhando...")
    if not meia_volta_e_alinhar(TEMPO_MEIA_VOLTA, TEMPO_ALINHAR_LINHA):
        print("⚠️ Não conseguiu alinhar após meia volta!")
    parar(0.2)
    
    # ===== PASSO 5: Modo CAPTURA =====
    print("📌 PASSO 5: Modo CAPTURA...")
    executar_captura()
    parar(0.3)
    
    # ===== PASSO 6: Seguir linha até perder novamente =====
    print("📌 PASSO 6: Seguindo linha até perder (2ª vez)...")
    linha_perdida = seguir_linha_ate_perder(TEMPO_SEGUIR_LINHA)
    if not linha_perdida:
        print("⚠️ Timeout: não perdeu a linha a tempo! Forçando parada...")
    parar(0.3)
    
    # ===== PASSO 7: Meia volta e alinhar =====
    print("📌 PASSO 7: Meia volta e alinhando (2ª vez)...")
    if not meia_volta_e_alinhar(TEMPO_MEIA_VOLTA, TEMPO_ALINHAR_LINHA):
        print("⚠️ Não conseguiu alinhar após meia volta!")
    parar(0.2)
    
    # ===== PASSO 8: Modo DESPEJO =====
    print("📌 PASSO 8: Modo DESPEJO...")
    executar_despejo()
    parar(0.3)
    
    print("✅ Ciclo completo finalizado!")
    parar()

# ===== Função para testes =====
def testar_movimentos():
    """Função para testar cada etapa individualmente"""
    print("🧪 Modo de teste - execute a função desejada:")
    print("  - girar_ate_linha(1)  : gira esquerda até linha")
    print("  - alinhar_com_linha() : alinha com a linha")
    print("  - seguir_linha_ate_perder() : segue até perder")
    print("  - meia_volta_e_alinhar() : meia volta + alinhar")
    print("  - executar_captura()  : executa captura")
    print("  - executar_despejo()  : executa despejo")
    print("  - executar_ciclo_completo() : executa tudo")

# ===== EXECUÇÃO PRINCIPAL =====
if __name__ == "__main__":
    # Aguarda o botão iniciar (se tiver)
    print("Aguardando botão para iniciar...")
    robo.iniciar()
    
    # Espera o botão ser pressionado (até 30 segundos)
    timeout = 150
    inicio = time.monotonic()
    while not robo.botao_pressionado and time.monotonic() - inicio < timeout:
        sleep(0.1)
    
    if robo.botao_pressionado:
        print("🔴 Botão pressionado! Iniciando...")
        sleep(0.5)
        
        # Executa o ciclo completo
        executar_ciclo_completo()
        
        print("🏁 Robô finalizou o ciclo!")
    else:
        print("⏰ Timeout: botão não foi pressionado!")