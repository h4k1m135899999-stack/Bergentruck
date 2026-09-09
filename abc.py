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
FRAMES_SEM_LINHA_PARA_PERDER = 8    # ⭐ REDUZIDO de 15 para 8
TEMPO_MINIMO_SEM_LINHA = 0.15        # ⭐ REDUZIDO de 0.3 para 0.15

# ⭐ NOVA CONSTANTE: Distância segura antes do obstáculo
DISTANCIA_SEGURA_OBSTACULO_MM = 80.0  # Para a 8cm antes do obstáculo

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
    """Gira até encontrar a linha."""
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

# ⭐ FUNÇÃO CORRIGIDA: Detecta obstáculo E perda de linha
def seguir_linha_ate_perder(tempo_max=12.0):
    """
    Segue a linha até:
    - Perder a linha (detectado mais rápido)
    - Encontrar um obstáculo (caixa de bombom)
    - Timeout
    """
    inicio = time.monotonic()
    frames_sem_linha = 0
    inicio_sem_linha = None
    frames_obstaculo = 0
    
    print("   🛑 Monitorando: linha, obstáculos...")
    
    while time.monotonic() - inicio < tempo_max:
        robo.atualizar()
        
        # ⭐ PRIORIDADE 1: Detectar obstáculo (caixa de bombom)
        if robo.tem_obstaculo():
            frames_obstaculo += 1
            
            # Confirma obstáculo após alguns frames
            if frames_obstaculo >= 2:
                print("🎯 OBSTÁCULO DETECTADO! Parando...")
                parar(0.1)
                
                # ⭐ Tenta recuar um pouco para não encostar
                mover(-0.2, -0.2, 0.2)
                parar(0.1)
                
                return False  # Retorna False indicando que parou por obstáculo
        else:
            frames_obstaculo = 0
        
        # ⭐ PRIORIDADE 2: Verificar se tem linha
        if robo.tem_linha():
            # Reset dos contadores se a linha voltou
            frames_sem_linha = 0
            inicio_sem_linha = None
            robo.seguir_linha()
            
        else:
            # Não tem linha - conta os frames (AGORA MAIS RÁPIDO)
            frames_sem_linha += 1
            if inicio_sem_linha is None:
                inicio_sem_linha = time.monotonic()
            
            # ⭐ PERDE MAIS RÁPIDO: 8 frames ou 0.15s
            if frames_sem_linha >= FRAMES_SEM_LINHA_PARA_PERDER or \
               (inicio_sem_linha and time.monotonic() - inicio_sem_linha > TEMPO_MINIMO_SEM_LINHA):
                print(f"⚠️ Perdeu linha! {frames_sem_linha} frames sem linha")
                parar(0.1)
                return True
            
            # Ainda não perdeu - tenta encontrar
            if hasattr(robo, '_ultimo_erro_linha'):
                erro = robo._ultimo_erro_linha
                if abs(erro) >= 0.4:
                    if erro > 0:
                        robo.set_motores(0.12, -0.12)
                    else:
                        robo.set_motores(-0.12, 0.12)
                else:
                    robo.set_motores(0.15, 0.15)
            else:
                robo.set_motores(0.12, 0.12)
            
        sleep(0.02)
    
    print("⚠️ Timeout: não perdeu a linha a tempo!")
    parar()
    return False

# ⭐ NOVA FUNÇÃO: Segue linha até encontrar obstáculo
def seguir_ate_obstaculo(tempo_max=10.0):
    """
    Segue a linha até encontrar um obstáculo (caixa de bombom).
    Retorna True se encontrou obstáculo, False se perdeu a linha ou timeout.
    """
    inicio = time.monotonic()
    frames_obstaculo = 0
    
    print("   🎯 Seguindo até encontrar caixa de bombom...")
    
    while time.monotonic() - inicio < tempo_max:
        robo.atualizar()
        
        # ⭐ Detecta obstáculo
        if robo.tem_obstaculo():
            frames_obstaculo += 1
            if frames_obstaculo >= 2:
                print("✅ OBSTÁCULO ENCONTRADO!")
                parar(0.1)
                return True
        else:
            frames_obstaculo = 0
        
        # Se perdeu a linha, algo deu errado
        if not robo.tem_linha():
            print("⚠️ Perdeu a linha antes do obstáculo!")
            parar(0.1)
            return False
        
        # Continua seguindo a linha
        robo.seguir_linha()
        sleep(0.02)
    
    print("⏰ Timeout procurando obstáculo!")
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

def executar_captura():
    """Executa a sequência de captura da vítima"""
    print("🔄 Iniciando CAPTURA...")
    
    print("📦 Pegando a caixa de bombom...")
    # ⭐ Movimento para pegar a caixa
    robo.garra("open")
    robo.alavanca("down")
    sleep(0.5)
    robo.garra("closed")
    sleep(0.5)
    robo.alavanca("up")
    robo.garra("open")
    
    print("✅ Captura finalizada!")
    return True

def executar_despejo():
    """Executa a sequência de despejo da vítima"""
    print("🔄 Iniciando DESPEJO...")
    robo.entregar_vitima()
    print("✅ Despejo finalizado!")

# ⭐ FUNÇÃO PRINCIPAL CORRIGIDA
def executar_ciclo_completo():
    """
    Ciclo completo com detecção de obstáculo.
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
    
    # ===== PASSO 3: Seguir linha até PERDER ou OBSTÁCULO =====
    print("📌 PASSO 3: Seguindo linha...")
    print("   🔍 Procurando: perda de linha OU obstáculo")
    
    # ⭐ USA A NOVA FUNÇÃO QUE DETECTA OBSTÁCULO
    resultado = seguir_linha_ate_perder(TEMPO_SEGUIR_LINHA)
    
    if resultado is None:
        print("⚠️ Tempo esgotado!")
        parar()
        return
    
    print(f"📍 Posição: x={robo.x:.1f}, y={robo.y:.1f}")
    
    # ⭐ Se parou por obstáculo, faz a captura
    if not resultado:  # False = parou por obstáculo
        print("📌 OBSTÁCULO DETECTADO - Iniciando captura!")
        
        # ===== PASSO 4: Captura =====
        print("📌 PASSO 4: Capturando caixa de bombom...")
        executar_captura()
        parar(0.3)
        
        # ===== PASSO 5: Meia volta =====
        print("📌 PASSO 5: Meia volta após captura...")
        mover(-0.3, -0.3, 0.3)  # Recua um pouco
        meia_volta_e_alinhar(TEMPO_MEIA_VOLTA, TEMPO_ALINHAR_LINHA)
        parar(0.2)
        
        # ===== PASSO 6: Voltar seguindo linha =====
        print("📌 PASSO 6: Voltando pela linha...")
        linha_perdida = seguir_linha_ate_perder(TEMPO_SEGUIR_LINHA)
        parar(0.3)
        
        # ===== PASSO 7: Meia volta e despejo =====
        print("📌 PASSO 7: Meia volta para despejo...")
        mover(-0.3, -0.3, 0.3)
        meia_volta_e_alinhar(TEMPO_MEIA_VOLTA, TEMPO_ALINHAR_LINHA)
        parar(0.2)
        
        # ===== PASSO 8: Despejo =====
        print("📌 PASSO 8: Despejando...")
        executar_despejo()
        
    else:
        print("⚠️ Perdeu a linha antes do obstáculo!")
        # Tenta se recuperar
    
    print("✅ Ciclo completo finalizado!")
    parar()

# ⭐ FUNÇÃO DE TESTE: Mostra se está vendo obstáculo
def testar_deteccao():
    """Testa se o robô está detectando o obstáculo (caixa de bombom)"""
    print("🧪 Testando detecção de obstáculo...")
    for _ in range(50):
        robo.atualizar()
        if robo.tem_obstaculo():
            print(f"✅ OBSTÁCULO DETECTADO! BBox: {robo.obstacle_bbox}")
        else:
            print("❌ Sem obstáculo")
        sleep(0.1)

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