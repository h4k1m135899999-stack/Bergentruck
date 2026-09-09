from robo import Robo
from time import sleep
import time
import math

robo = Robo()

# Constantes de tempo
TEMPO_GIRO_ESQUERDA = 0.6
TEMPO_MEIA_VOLTA = 1.5
TEMPO_ALINHAR_LINHA = 4.0
TEMPO_SEGUIR_LINHA = 10.0
TEMPO_CAPTURA = 2.0
TEMPO_DESPEJO = 2.0

# ⭐ CONSTANTES PARA DETECÇÃO DE PERDA DE LINHA
FRAMES_SEM_LINHA_PARA_PERDER = 8    # Quantos frames sem linha antes de considerar perdida
TEMPO_MINIMO_SEM_LINHA = 0.15       # Tempo mínimo sem linha antes de considerar perdida

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

def girar_ate_linha(direcao=1, tempo_max=4.0):
    """
    Gira até encontrar a linha.
    direcao = 1: esquerda, direcao = -1: direita
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

# ⭐ FUNÇÃO SIMPLES: Segue linha até perder
def seguir_linha_ate_perder(tempo_max=10.0):
    """
    Segue a linha até perder realmente.
    """
    inicio = time.monotonic()
    frames_sem_linha = 0
    inicio_sem_linha = None
    
    print("   🟢 Seguindo linha...")
    
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
                print(f"⚠️ Perdeu linha! {frames_sem_linha} frames sem linha")
                parar(0.1)
                return True
            
            # Ainda não perdeu - tenta encontrar a linha
            if hasattr(robo, '_ultimo_erro_linha'):
                erro = robo._ultimo_erro_linha
                if abs(erro) >= 0.4:  # Curva fechada
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

# ⭐ FUNÇÃO SIMPLES: Meia volta e alinha
def meia_volta_e_alinhar(tempo_giro=1.2, tempo_alinhar=4.0):
    """Dá meia volta e depois se alinha com a linha."""
    print("🔄 Dando meia volta...")
    
    # Gira 180° (meia volta)
    girar(1, tempo_giro)
    parar(0.2)
    
    # Procura e alinha com a linha
    print("🔍 Procurando linha após meia volta...")
    if girar_ate_linha(direcao=-1, tempo_max=tempo_alinhar):
        print("✅ Linha encontrada após meia volta!")
        return alinhar_com_linha(tempo_max=tempo_alinhar)
    
    # Se não encontrou, tenta o outro lado
    print("🔄 Tentando o outro lado...")
    if girar_ate_linha(direcao=1, tempo_max=2.0):
        print("✅ Linha encontrada no outro lado!")
        return alinhar_com_linha(tempo_max=2.0)
    
    print("❌ Não conseguiu encontrar a linha após meia volta!")
    return False

# ⭐ FUNÇÃO SIMPLES: Recua e faz meia volta
def recuar_e_meia_volta(tempo_recuo=0.3, tempo_giro=1.2):
    """
    Recua um pouco e depois dá meia volta.
    """
    print("↩️ Recuando um pouco...")
    mover(-0.3, -0.3, tempo_recuo)
    parar(0.2)
    
    return meia_volta_e_alinhar(tempo_giro, TEMPO_ALINHAR_LINHA)

# ⭐ FUNÇÃO PRINCIPAL DO CICLO
def executar_ciclo_completo():
    """
    Ciclo completo:
    1. Anda pra frente
    2. Gira até alinhar com a linha
    3. Segue linha até perder
    4. Recua e dá meia volta
    5. Segue linha até perder novamente
    6. Recua e dá meia volta
    """
    
    print("🚀 Iniciando ciclo completo!")
    print("=" * 50)
    
    # ===== PASSO 1: Andar pra frente =====
    print("📌 PASSO 1: Andando pra frente...")
    mover(0.4, 0.4, 0.95)
    parar(0.2)
    
    # ===== PASSO 2: Girar até alinhar com a linha =====
    print("📌 PASSO 2: Girando até alinhar com a linha...")
    
    # Tenta girar para esquerda primeiro
    if not girar_ate_linha(direcao=1, tempo_max=TEMPO_ALINHAR_LINHA):
        print("⚠️ Não encontrou linha para esquerda! Tentando direita...")
        girar_ate_linha(direcao=-1, tempo_max=2.0)
    
    alinhar_com_linha(TEMPO_ALINHAR_LINHA)
    parar(0.2)
    
    print(f"📍 Posição atual: x={robo.x:.1f}, y={robo.y:.1f}")
    print("=" * 50)
    
    # ===== PASSO 3: Seguir linha até PERDER =====
    print("📌 PASSO 3: Seguindo linha até perder...")
    linha_perdida = seguir_linha_ate_perder(TEMPO_SEGUIR_LINHA)
    
    if not linha_perdida:
        print("⚠️ Timeout: não perdeu a linha a tempo! Forçando parada...")
    parar(0.3)
    
    print(f"📍 Posição após perder linha: x={robo.x:.1f}, y={robo.y:.1f}")
    print("=" * 50)
    
    # ===== PASSO 4: Recuar e dar meia volta =====
    print("📌 PASSO 4: Recuando e dando meia volta...")
    
    # Recua um pouco
    mover(-0.3, -0.3, 0.3)
    parar(0.2)
    
    # Dá meia volta e alinha com a linha
    if not meia_volta_e_alinhar(TEMPO_MEIA_VOLTA, TEMPO_ALINHAR_LINHA):
        print("⚠️ Não conseguiu alinhar após meia volta!")
        # Tenta com recuo
        if recuar_e_meia_volta(0.2, TEMPO_MEIA_VOLTA):
            print("✅ Conseguiu alinhar com recuo!")
    
    parar(0.2)
    print(f"📍 Posição após meia volta: x={robo.x:.1f}, y={robo.y:.1f}")
    print("=" * 50)
    
    # ===== PASSO 5: Seguir linha até perder novamente =====
    print("📌 PASSO 5: Seguindo linha até perder (2ª vez)...")
    linha_perdida = seguir_linha_ate_perder(TEMPO_SEGUIR_LINHA)
    
    if not linha_perdida:
        print("⚠️ Timeout: não perdeu a linha a tempo! Forçando parada...")
    parar(0.3)
    
    print(f"📍 Posição após perder linha (2ª vez): x={robo.x:.1f}, y={robo.y:.1f}")
    print("=" * 50)
    
    # ===== PASSO 6: Recuar e dar meia volta novamente =====
    print("📌 PASSO 6: Recuando e dando meia volta (2ª vez)...")
    
    # Recua um pouco
    mover(-0.3, -0.3, 0.3)
    parar(0.2)
    
    # Dá meia volta e alinha com a linha
    if not meia_volta_e_alinhar(TEMPO_MEIA_VOLTA, TEMPO_ALINHAR_LINHA):
        print("⚠️ Não conseguiu alinhar após meia volta!")
        recuar_e_meia_volta(0.2, TEMPO_MEIA_VOLTA)
    
    parar(0.2)
    print(f"📍 Posição final: x={robo.x:.1f}, y={robo.y:.1f}")
    
    print("=" * 50)
    print("✅ Ciclo completo finalizado!")
    parar()

# ⭐ FUNÇÃO PARA DIAGNÓSTICO
def diagnosticar_linha():
    """Diagnóstico rápido do estado da linha."""
    robo.atualizar()
    print("\n📊 DIAGNÓSTICO DA LINHA:")
    print(f"   Linha encontrada: {robo.tem_linha()}")
    print(f"   Erro: {robo.erro_linha:.3f}")
    print(f"   Heading: {math.degrees(robo.heading):.1f}°")
    if hasattr(robo, '_ultimo_erro_linha'):
        print(f"   Último erro: {robo._ultimo_erro_linha:.3f}")
    if hasattr(robo, '_frames_sem_linha'):
        print(f"   Frames sem linha: {robo._frames_sem_linha}")
    print("")

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
        
        # ⭐ Opcional: fazer diagnóstico antes de começar
        # diagnosticar_linha()
        
        executar_ciclo_completo()
        print("🏁 Robô finalizou o ciclo!")
    else:
        print("⏰ Timeout: botão não foi pressionado!")