from robo import Robo
from time import sleep
import time
import math

robo = Robo()

# Constantes de tempo (ajuste conforme necessário)
TEMPO_GIRO_ESQUERDA = 0.6
TEMPO_MEIA_VOLTA = 1.5
TEMPO_ALINHAR_LINHA = 6.0
TEMPO_SEGUIR_LINHA = 10.0
TEMPO_CAPTURA = 2.0
TEMPO_DESPEJO = 2.0

# ⭐ CONSTANTES PARA GAPS/CURVAS
FRAMES_SEM_LINHA_PARA_PERDER = 15
TEMPO_MINIMO_SEM_LINHA = 0.3

# ⭐ NOVAS CONSTANTES PARA MEIA VOLTA
VELOCIDADE_GIRO = 0.25          # Velocidade para girar
PRECISAO_ANGULO = math.radians(3)  # Tolerância de 3°

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

# ⭐ NOVA FUNÇÃO: Meia volta usando ODOMETRIA
def meia_volta_odometria(direcao=1, vel=0.25, tolerancia=math.radians(3)):
    """
    Dá meia volta usando a odometria.
    direcao = 1: vira para esquerda
    direcao = -1: vira para direita
    Retorna True se completou a meia volta, False se timeout
    """
    inicio = time.monotonic()
    angulo_inicial = robo.theta
    angulo_alvo = angulo_inicial + (math.pi * direcao)  # 180° na direção escolhida
    
    print(f"🔄 Iniciando meia volta: de {math.degrees(angulo_inicial):.1f}° para {math.degrees(angulo_alvo):.1f}°")
    
    # Tempo máximo para a meia volta (8 segundos é suficiente para 180°)
    timeout = 8.0
    
    while time.monotonic() - inicio < timeout:
        robo.atualizar()
        
        # Calcula o erro angular
        erro = robo.theta - angulo_alvo
        erro = math.atan2(math.sin(erro), math.cos(erro))  # Normaliza entre -pi e pi
        
        # Se chegou próximo o suficiente, para
        if abs(erro) < tolerancia:
            parar(0.2)
            print(f"✅ Meia volta completada! Ângulo final: {math.degrees(robo.theta):.1f}°")
            return True
        
        # Velocidade ajustável: mais rápido no começo, mais lento no final
        fator_vel = min(1.0, abs(erro) / 0.5)  # 0.5 rad ~ 28°
        vel_atual = max(0.08, vel * max(0.3, fator_vel))
        
        # Gira na direção correta
        if erro > 0:  # Precisa virar para ESQUERDA
            robo.set_motores(-vel_atual, vel_atual)
        else:  # Precisa virar para DIREITA
            robo.set_motores(vel_atual, -vel_atual)
        
        # Mostra progresso a cada 45°
        angulo_atual = math.degrees(robo.theta - angulo_inicial)
        if abs(angulo_atual) % 45 < 1:
            print(f"   Progresso: {abs(angulo_atual):.1f}°")
        
        sleep(0.02)
    
    print(f"⚠️ Timeout na meia volta! Ângulo final: {math.degrees(robo.theta):.1f}°")
    parar()
    return False

# ⭐ NOVA FUNÇÃO: Meia volta + busca pela linha
def meia_volta_e_procurar_linha(direcao=1, tempo_max=5.0):
    """
    Dá meia volta usando odometria e depois PROCURA a linha.
    Retorna True se encontrou a linha, False se não.
    """
    # Passo 1: Dá a meia volta
    if not meia_volta_odometria(direcao):
        print("⚠️ Meia volta falhou!")
        return False
    
    parar(0.2)
    
    # Passo 2: Procura a linha girando lentamente
    print("🔍 Procurando a linha após meia volta...")
    inicio = time.monotonic()
    
    # Tenta encontrar a linha girando para um lado
    for tentativa in range(2):
        direcao_busca = 1 if tentativa == 0 else -1
        inicio_busca = time.monotonic()
        
        while time.monotonic() - inicio_busca < tempo_max / 2:
            robo.atualizar()
            
            if robo.tem_linha():
                print("✅ Linha encontrada!")
                parar(0.1)
                return True
            
            # Gira lentamente procurando
            robo.set_motores(-0.12 * direcao_busca, 0.12 * direcao_busca)
            sleep(0.02)
        
        # Se não encontrou, para e tenta o outro lado
        parar(0.1)
    
    print("⚠️ Não encontrou a linha após meia volta!")
    parar()
    return False

# ⭐ FUNÇÃO ALTERNATIVA: Meia volta com movimento de ré antes
def meia_volta_com_recuo():
    """
    Dá ré um pouco, depois faz meia volta e procura a linha.
    Útil quando o robô está muito perto da linha.
    """
    print("↩️ Recuando antes da meia volta...")
    mover(-0.2, -0.2, 0.3)  # Ré por 0.3s
    parar(0.2)
    
    return meia_volta_e_procurar_linha()

def girar_ate_linha(direcao=1, tempo_max=3.0):
    """Gira até encontrar a linha."""
    inicio = time.monotonic()
    while time.monotonic() - inicio < tempo_max:
        robo.atualizar()
        if robo.tem_linha():
            parar(0.1)
            return True
        if direcao == 1:
            robo.set_motores(-0.25, 0.15)
        else:
            robo.set_motores(0.25, -0.15)
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

def seguir_linha_ate_perder(tempo_max=12.0):
    """Segue a linha até PERDER REALMENTE."""
    inicio = time.monotonic()
    frames_sem_linha = 0
    inicio_sem_linha = None
    
    while time.monotonic() - inicio < tempo_max:
        robo.atualizar()
        
        if robo.tem_linha():
            frames_sem_linha = 0
            inicio_sem_linha = None
            robo.seguir_linha()
            
        else:
            frames_sem_linha += 1
            if inicio_sem_linha is None:
                inicio_sem_linha = time.monotonic()
            
            if frames_sem_linha >= FRAMES_SEM_LINHA_PARA_PERDER or \
               (inicio_sem_linha and time.monotonic() - inicio_sem_linha > TEMPO_MINIMO_SEM_LINHA):
                print(f"⚠️ Perdeu linha! {frames_sem_linha} frames sem linha")
                parar(0.1)
                return True
            
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

def executar_captura():
    """Executa a sequência de captura da vítima"""
    print("🔄 Iniciando CAPTURA...")
    
    # ⭐ MODO MANUAL: você pode implementar a captura aqui
    print("📦 Abaixando garra para pegar cubos...")
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

# ⭐ CICLO COMPLETO COM MEIA VOLTA FUNCIONAL
def executar_ciclo_completo():
    """
    Executa o ciclo completo com meia volta usando odometria.
    """
    
    print("🚀 Iniciando ciclo completo!")
    
    # ===== PASSO 1: Andar pra frente =====
    print("📌 PASSO 1: Andando pra frente...")
    mover(0.5, 0.4, 1.0)
    parar(0.2)
    
    # ===== PASSO 2: Girar até alinhar com a linha =====
    print("📌 PASSO 2: Girando até alinhar com a linha...")
    if not girar_ate_linha(direcao=1, tempo_max=TEMPO_ALINHAR_LINHA):
        print("⚠️ Não encontrou linha! Tentando direção oposta...")
        girar_ate_linha(direcao=-1, tempo_max=2.0)
    
    alinhar_com_linha(TEMPO_ALINHAR_LINHA)
    parar(0.2)
    
    # ===== PASSO 3: Seguir linha até PERDER =====
    print("📌 PASSO 3: Seguindo linha até perder...")
    linha_perdida = seguir_linha_ate_perder(TEMPO_SEGUIR_LINHA)
    if not linha_perdida:
        print("⚠️ Timeout: não perdeu a linha a tempo!")
    parar(0.3)
    
    print(f"📍 Posição: x={robo.x:.1f}, y={robo.y:.1f}")
    
    # ===== PASSO 4: Meia VOLTA com odometria =====
    print("📌 PASSO 4: Dando meia volta...")
    
    # ⭐ OPÇÃO 1: Meia volta simples
    if meia_volta_e_procurar_linha(direcao=1):
        alinhar_com_linha(3.0)
    else:
        # ⭐ OPÇÃO 2: Tenta com recuo
        print("🔄 Tentando meia volta com recuo...")
        if meia_volta_com_recuo():
            alinhar_com_linha(3.0)
        else:
            print("⚠️ Não conseguiu encontrar a linha após meia volta!")
    
    parar(0.2)
    
    # ===== PASSO 5: Modo CAPTURA =====
    print("📌 PASSO 5: Modo CAPTURA...")
    executar_captura()
    parar(0.3)
    
    # ===== PASSO 6: Seguir linha até perder novamente =====
    print("📌 PASSO 6: Seguindo linha até perder (2ª vez)...")
    linha_perdida = seguir_linha_ate_perder(TEMPO_SEGUIR_LINHA)
    if not linha_perdida:
        print("⚠️ Timeout: não perdeu a linha a tempo!")
    parar(0.3)
    
    print(f"📍 Posição: x={robo.x:.1f}, y={robo.y:.1f}")
    
    # ===== PASSO 7: Meia volta novamente =====
    print("📌 PASSO 7: Meia volta (2ª vez)...")
    if meia_volta_e_procurar_linha(direcao=1):
        alinhar_com_linha(3.0)
    else:
        meia_volta_com_recuo()
    parar(0.2)
    
    # ===== PASSO 8: Modo DESPEJO =====
    print("📌 PASSO 8: Modo DESPEJO...")
    executar_despejo()
    parar(0.3)
    
    print("✅ Ciclo completo finalizado!")
    parar()

# ===== TESTE RÁPIDO DA MEIA VOLTA =====
def testar_meia_volta():
    """Função para testar apenas a meia volta"""
    print("🧪 Testando meia volta...")
    robo.atualizar()
    print(f"Ângulo inicial: {math.degrees(robo.theta):.1f}°")
    
    if meia_volta_e_procurar_linha(direcao=1):
        print("✅ Meia volta funcionou!")
    else:
        print("❌ Meia volta falhou!")
    
    print(f"Ângulo final: {math.degrees(robo.theta):.1f}°")

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