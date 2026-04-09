import sys
import configparser

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
        est_dict['LOCATION_AREA'] = config.getint(section, 'LOCATION_AREA')
        est_dict['NOISE_FLOOR'] = config.getfloat(section, 'NOISE_FLOOR')
        
        cord_str = config.get(section, 'CORD').replace('(', '').replace(')', '')
        x, y = map(float, cord_str.split(','))
        est_dict['CORD'] = (x, y)
        
        ESTACOES_CONFIG.append(est_dict)