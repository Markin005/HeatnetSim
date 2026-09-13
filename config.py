import sys
import configparser
import ast  # ADICIONADO: Necessário para converter a string do .ini em uma lista real de tuplas

# 1. Verifica se o usuário digitou o nome do arquivo no terminal
if len(sys.argv) < 2:
    print("ERRO: Nenhum arquivo de configuração foi fornecido!")
    print("Uso correto: python main.py <nome_do_arquivo.ini>")
    sys.exit(1) # Encerra o programa imediatamente

# 2. Pega o nome do arquivo digitado
arquivo_escolhido = sys.argv[1]

print(f"Carregando configurações de: {arquivo_escolhido}")

# 3. Cria UM ÚNICO leitor e lê o arquivo escolhido
config = configparser.ConfigParser()
config.read(arquivo_escolhido)

# ==========================================
# CONFIGURAÇÕES DE TEMPO E INTERFACE
# ==========================================

# A taxa de atualização da interface gráfica (em milissegundos)
# 100 ms = a tela pisca a cada 0.1 segundos reais
TICK_TKINTER_MS = 1

# ==========================================
# CÁLCULO AUTOMÁTICO DO DELTA T (O "Quantum")
# ==========================================
# Ex: 100 / 1000 = 0.1 segundos virtuais por rodada.
DELTA_T = 0.1

# ==========================================
# LENDO CONFIGURAÇÕES DA ÁREA (CANVAS)
# ==========================================
AREA_LARGURA = config.getint('CANVAS', 'AREA_LARGURA')
AREA_ALTURA = config.getint('CANVAS', 'AREA_ALTURA')

# ==========================================
# LENDO CONFIGURAÇÕES DA UE
# ==========================================
UE_VELOCIDADE = config.getfloat('UE', 'UE_VELOCIDADE')
UE_RAIO = config.getint('UE', 'UE_RAIO')
GANHO_ANTENA_RECEPCAO = config.getfloat('UE', 'GANHO_ANTENA_RECEPCAO')
ALTURA_ANTENA_MOVEL = config.getfloat('UE', 'ALTURA_ANTENA_MOVEL')
quantidade_ue = config.getint('UE', 'QUANTIDADE_UE')

# ==========================================
# LENDO CONFIGURAÇÕES GERAIS DAS ESTAÇÕES
# ==========================================
ESTACAO_SIMBOLO_TAMANHO = config.getint('Configuracoes_Gerais', 'ESTACAO_SIMBOLO_TAMANHO')
NUMERO_VIZINHAS = config.getint('Configuracoes_Gerais', 'NUMERO_VIZINHAS')

INTERFACE_GRAFICA = config.getboolean('Configuracoes_Gerais', 'INTERFACE')

# Lê se a posição é aleatória ou fixa (padrão é False caso não exista no .ini)
POSICAO_ALEATORIA = config.getboolean('Configuracoes_Gerais', 'POSICAO_ALEATORIA', fallback=False)

MODO_SIMULACAO = config.get('Configuracoes_Gerais', 'MODO_SIMULACAO', fallback='forca_bruta').strip().lower()
NUM_SIMULACOES_ESTATISTICA = config.getint('Configuracoes_Gerais', 'NUM_SIMULACOES_ESTATISTICA', fallback=5)

# ADICIONADO: Lê a lista de posições fixas do .ini e converte de string para uma lista de tuplas
posicoes_str = config.get('Configuracoes_Gerais', 'POSICOES_FIXAS', fallback='[(100,100), (200,200), (300,300)]')
POSICOES_FIXAS = ast.literal_eval(posicoes_str)

# ==========================================
# LENDO ESTAÇÕES INDIVIDUAIS
# ==========================================
ESTACOES_CONFIG = []

# Varre todas as seções do arquivo que abrimos lá em cima
for section in config.sections():
    if section.startswith('Estacao'):
        est_dict = {}
        est_dict['POTENCIA_TRANSMITIDA'] = config.getfloat(section, 'POTENCIA_TRANSMITIDA')
        est_dict['GANHO_ANTENA_TRANSMISSAO'] = config.getfloat(section, 'GANHO_ANTENA_TRANSMISSAO')
        est_dict['ALTURA_ANTENA_ESTACAO'] = config.getfloat(section, 'ALTURA_ANTENA_ESTACAO')
        est_dict['FREQUENCIA'] = config.getfloat(section, 'FREQUENCIA')
        est_dict['HISTERESE'] = config.getfloat(section, 'HISTERESE')
        est_dict['NOISE_FLOOR'] = config.getfloat(section, 'NOISE_FLOOR')
        
        # Lê o TAC como inteiro
        est_dict['TAC'] = config.getint(section, 'TAC')
        
        # Lê a TAC_LIST como string, separa por vírgula e converte para lista de inteiros
        tac_list_str = config.get(section, 'TAC_LIST')
        est_dict['TAC_LIST'] = [int(x.strip()) for x in tac_list_str.split(',')]
        
        # REMOVIDO: A leitura individual de 'CORD' foi removida daqui, pois agora as 
        # posições são injetadas diretamente pelo main.py usando a lista POSICOES_FIXAS.

        # ==========================================
        # LENDO CONFIGURAÇÕES DE FADING
        # ==========================================
        # Usa 'fallback' para não dar erro se o arquivo .ini não tiver essas linhas
        est_dict['FADING_HABILITADO'] = config.getboolean(section, 'FADING_HABILITADO', fallback=False)
        est_dict['FADING_SIGMA_DB'] = config.getfloat(section, 'FADING_SIGMA_DB', fallback=8.0)
        est_dict['FADING_TEMPO_CORRELACAO'] = config.getfloat(section, 'FADING_TEMPO_CORRELACAO', fallback=5.0)
        est_dict['FADING_TEMPO_ESTABILIDADE'] = config.getfloat(section, 'FADING_TEMPO_ESTABILIDADE', fallback=0.5)
        
        ESTACOES_CONFIG.append(est_dict)