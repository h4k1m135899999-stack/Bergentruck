from robo import Robo
from time import sleep
import time
import math

robo = Robo()

# Constantes de tempo (ajuste conforme necessário)
TEMPO_GIRO_ESQUERDA = 0.6
TEMPO_MEIA_VOLTA = 1.5
TEMPO_ALINHAR_LINHA = 6.0
TEMPO_SEGUIR_LINHA = 10.0      # Aumentei o tempo máximo
TEMPO_CAPTURA = 2.0
TEMPO_DESPEJO = 2.0

# ⭐ NOVAS CONSTANTES PARA GAPS/CURVAS
FRAMES_SEM_LINHA_PARA_PERDER = 15   # Quantos frames sem linha antes de considerar perdida
TEMPO_MINIMO_SEM_LINHA = 0.3        # Tempo mínimo sem linha antes de considerar perdida

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
    """Alinha o robô com a linha usando o heading da visão."""
    inicio = time.monotonic()
    while time.monotonic() - inicio < tempo_max:
        robo.atualizar()
        
        if not robo.tem_linha():
            continue
            
        erro = robo.heading
        
        if abs(erro) < math.radians(5):
            parar(0.1)
            return True
            
        if erro > 0:
            robo.set_motores(-0.12, 0.12)
        else:
            robo.set_motores(0.12, -0.12)
        sleep(0.02)
    parar()
    return False

# ⭐ FUNÇÃO MELHORADA: Segue linha até PERDER REALMENTE
def seguir_linha_ate_perder(tempo_max=12.0):
    """
    Segue a linha até PERDER REALMENTE (não apenas gaps/curvas).
    Usa contador de frames sem linha para evitar paradas prematuras.
    Retorna True se perdeu a linha, False se timeout
    """
    inicio = time.monotonic()
    frames_sem_linha = 0
    inicio_sem_linha = None
    
    while time.monotonic() - inicio < tempo_max:
        robo.atualizar()
        
        # Verifica se tem linha
        if robo.tem_linha():
            # Reset dos contadores se a linha voltou
            frames_sem_linha = 0
            inicio_sem_linha = None
            robo.seguir_linha()
            
        else:
            # Não tem linha - conta os frames
            frames_sem_linha += 1
            if inicio_sem_linha is None:
                inicio_sem_linha = time.monotonic()
            
            # ⭐ SÓ PERDE QUANDO FICA MUITO TEMPO SEM LINHA
            if frames_sem_linha >= FRAMES_SEM_LINHA_PARA_PERDER or \
               (inicio_sem_linha and time.monotonic() - inicio_sem_linha > TEMPO_MINIMO_SEM_LINHA):
                print(f"⚠️ Perdeu linha! {frames_sem_linha} frames sem linha, {time.monotonic() - inicio_sem_linha:.2f}s")
                parar(0.1)
                return True
            
            # Ainda não perdeu - continua tentando encontrar
            # ⭐ Usa o último erro conhecido para continuar seguindo
            if hasattr(robo, '_ultimo_erro_linha'):
                erro = robo._ultimo_erro_linha
                if abs(erro) >= 0.4:  # Curva fechada
                    # Gira na direção da curva
                    if erro > 0:
                        robo.set_motores(0.12, -0.12)
                    else:
                        robo.set_motores(-0.12, 0.12)
                else:
                    # Gap pequeno - continua reto
                    robo.set_motores(0.15, 0.15)
            else:
                robo.set_motores(0.12, 0.12)
            
        sleep(0.02)
    
    print("⚠️ Timeout: não perdeu a linha a tempo!")
    parar()
    return False

def meia_volta_e_alinhar(tempo_giro=1.2, tempo_alinhar=3.0):
    """Dá meia volta e depois se alinha com a linha."""
    # Gira 180° (meia volta)
    girar(1, tempo_giro)
    parar(0.2)
    
    # Procura e alinha com a linha
    if girar_ate_linha(direcao=-1, tempo_max=tempo_alinhar):
        return alinhar_com_linha(tempo_max=tempo_alinhar)
    
    return False

# ⭐ NOVA FUNÇÃO: Verifica se o robô realmente está pronto para capturar
def esperar_vitima_ou_linha(tempo_max=8.0):
    """
    Espera até encontrar uma vítima OU perder a linha.
    Usado para garantir que o robô chegue até a vítima.
    """
    inicio = time.monotonic()
    while time.monotonic() - inicio < tempo_max:
        robo.atualizar()
        
        # Se encontrou vítima - captura!
        if robo.tem_vitima():
            print("🎯 Vítima encontrada!")
            return "vitima"
        
        # Se perdeu a linha - algo deu errado
        if not robo.tem_linha():
            print("⚠️ Perdeu a linha antes de encontrar a vítima!")
            return "linha_perdida"
        
        # Continua seguindo a linha
        robo.seguir_linha()
        sleep(0.02)
    
    print("⏰ Timeout esperando vítima!")
    return "timeout"

def executar_captura():
    """Executa a sequência de captura da vítima"""
    print("🔄 Iniciando CAPTURA...")
    
    # ⭐ ANTES DE CAPTURAR: espera encontrar a vítima ou a linha
    resultado = esperar_vitima_ou_linha(6.0)
    
    if resultado == "vitima":
        # Centraliza e captura
        print("🎯 Centralizando na vítima...")
        inicio = time.monotonic()
        while time.monotonic() - inicio < 3.0 and robo.tem_vitima():
            robo.atualizar()
            if robo.centralizar_vitima():
                break
            sleep(0.02)
        
        robo.capturar_vitima()
        print("✅ Captura finalizada!")
        return True
    else:
        print("❌ Não encontrou vítima! Pulando captura...")
        return False

def executar_despejo():
    """Executa a sequência de despejo da vítima"""
    print("🔄 Iniciando DESPEJO...")
    robo.entregar_vitima()
    print("✅ Despejo finalizado!")

# ⭐ FUNÇÃO MELHORADA: Ciclo completo com verificação
def executar_ciclo_completo():
    """
    Executa o ciclo completo:
    1. Anda pra frente
    2. Gira pra esquerda até alinhar com a linha
    3. Segue linha até perder (realmente)
    4. Meia volta e alinha
    5. Modo CAPTURA (com verificação)
    6. Segue linha até perder
    7. Meia volta e alinha
    8. Modo DESPEJO
    """
    
    print("🚀 Iniciando ciclo completo!")
    
    # ===== PASSO 1: Andar pra frente =====
    print("📌 PASSO 1: Andando pra frente...")
    mover(0.4, 0.4, 0.95)
    parar(0.2)
    
    # ===== PASSO 2: Girar até alinhar com a linha =====
    print("📌 PASSO 2: Girando até alinhar com a linha...")
    if not girar_ate_linha(direcao=1, tempo_max=TEMPO_ALINHAR_LINHA):
        print("⚠️ Não encontrou linha! Tentando direção oposta...")
        girar_ate_linha(direcao=-1, tempo_max=2.0)
    
    alinhar_com_linha(TEMPO_ALINHAR_LINHA)
    parar(0.2)
    
    # ===== PASSO 3: Seguir linha até PERDER REALMENTE =====
    print("📌 PASSO 3: Seguindo linha até perder...")
    print("   ⚠️ Ignorando gaps/curvas curtas (< 15 frames)...")
    
    linha_perdida = seguir_linha_ate_perder(TEMPO_SEGUIR_LINHA)
    if not linha_perdida:
        print("⚠️ Timeout: não perdeu a linha a tempo! Forçando parada...")
    parar(0.3)
    
    # ⭐ Debug: mostra onde o robô está
    print(f"📍 Posição: x={robo.x:.1f}, y={robo.y:.1f}")
    
    # ===== PASSO 4: Meia volta e alinhar =====
    print("📌 PASSO 4: Meia volta e alinhando...")
    mover(-0.5, -0.4, 0.3)
    mover(-0.25, 0.2, 1.2)
    '''
    if not meia_volta_e_alinhar(TEMPO_MEIA_VOLTA, TEMPO_ALINHAR_LINHA):
        print("⚠️ Não conseguiu alinhar após meia volta!")
    '''
    parar(0.2)
    
    # ===== PASSO 5: Modo CAPTURA (com verificação) =====
    print("📌 PASSO 5: Modo CAPTURA...")
    print("   🎯 Aguardando vítima ou linha...")
    #ativar depois

    
    #capturou = executar_captura()
    #if not capturou:
    #    print("⚠️ Captura não realizada! Continuando...")
    parar(0.3)
    
    # ===== PASSO 6: Seguir linha até perder novamente =====
    print("📌 PASSO 6: Seguindo linha até perder (2ª vez)...")
    linha_perdida = seguir_linha_ate_perder(TEMPO_SEGUIR_LINHA)
    if not linha_perdida:
        print("⚠️ Timeout: não perdeu a linha a tempo! Forçando parada...")
    parar(0.3)
    
    print(f"📍 Posição: x={robo.x:.1f}, y={robo.y:.1f}")
    
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

# ⭐ NOVA FUNÇÃO: Verifica se a linha está realmente perdida
def diagnosticar_linha():
    """Função de diagnóstico para ver o estado da linha"""
    robo.atualizar()
    print(f"Linha encontrada: {robo.tem_linha()}")
    print(f"Erro: {robo.erro_linha}")
    print(f"Heading: {math.degrees(robo.heading):.1f}°")
    if hasattr(robo, '_frames_sem_linha'):
        print(f"Frames sem linha: {robo._frames_sem_linha}")

# ===== EXECUÇÃO PRINCIPAL =====
if __name__ == "__main__":
    print("Aguardando botão para iniciar...")
    robo.iniciar()
    
    timeout = 30
    inicio = time.monotonic()
    while not robo.botao_pressionado and time.monotonic() - inicio < timeout:
        sleep(0.1)
    
    if robo.botao_pressionado:
        print("🔴 Botão pressionado! Iniciando...")
        sleep(0.5)
        executar_ciclo_completo()
        print("🏁 Robô finalizou o ciclo!")
    else:
        print("⏰ Timeout: botão não foi pressionado!")
