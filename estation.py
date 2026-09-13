import config
import math
from fading import GaussianFadingModel  # Importando o modelo de desvanecimento

class estation:
    def __init__(self, dicionario_config):
        self.x = dicionario_config['CORD'][0]
        self.y = dicionario_config['CORD'][1]
        
        # MODIFICADO: Substituição de LOCATION_AREA por TAC e TAC_LIST
        self.tac = dicionario_config['TAC']
        self.tac_list = dicionario_config['TAC_LIST']
        
        self.potencia = dicionario_config['POTENCIA_TRANSMITIDA']
        self.ganho_antena_transmissao = dicionario_config['GANHO_ANTENA_TRANSMISSAO']
        self.altura_antena = dicionario_config['ALTURA_ANTENA_ESTACAO']
        self.frequencia = dicionario_config['FREQUENCIA']
        self.histerese = dicionario_config['HISTERESE']
        self.noise_floor = dicionario_config['NOISE_FLOOR']
        
        self.vizinhos = []
        self.numero_ues_acampadas = 0

        # ==========================================
        # INICIALIZAÇÃO DO FADING
        # ==========================================
        # Usa .get() para não quebrar o código caso você esqueça de colocar no config
        self.modelo_fading = GaussianFadingModel(
            habilitado=dicionario_config.get('FADING_HABILITADO', False),
            sigma_db=dicionario_config.get('FADING_SIGMA_DB', 8.0), # 8dB é padrão para área urbana
            tempo_correlacao_s=dicionario_config.get('FADING_TEMPO_CORRELACAO', 5.0),
            tempo_estabilidade_s=dicionario_config.get('FADING_TEMPO_ESTABILIDADE', 0.5),
            delta_t_s=getattr(config, 'DELTA_T', 1.0), # Pega o passo de tempo da simulação
            seed=dicionario_config.get('FADING_SEED', None)
        )

    def calcular_estacoes_vizinhas(self, todas_as_estacoes):
        distancias = []

        for outra in todas_as_estacoes:
            if self is outra:
                continue

            d = math.dist(
                (self.x, self.y),
                (outra.get_x(), outra.get_y())
            )
            distancias.append((d, outra))

        # Ordenar por menor distância
        distancias.sort(key=lambda x: x[0])

        self.vizinhos = [
            outra for _, outra in distancias[:config.NUMERO_VIZINHAS]
        ]

    def incrementar_ue(self):
        self.numero_ues_acampadas += 1

    def decrementar_ue(self):
        if self.numero_ues_acampadas > 0:
            self.numero_ues_acampadas -= 1
            
    def paging(self):
        pass

    # ==========================================
    # NOVO: MÉTODO PARA APLICAR FADING
    # ==========================================
    def aplicar_fading(self, rsrp_base, ue_id):
        """
        Recebe o RSRP calculado pelo modelo de propagação (ex: Okumura-Hata)
        e adiciona o desvanecimento Gaussiano específico deste UE.
        """
        return self.modelo_fading.aplicar(rsrp_base, link_id=ue_id)

    # ==========================================
    # GETTERS 
    # ==========================================
    def get_x(self): return self.x
    def get_y(self): return self.y
    def get_altura_antena(self): return self.altura_antena
    def get_ganho_antena_transmissao(self): return self.ganho_antena_transmissao
    def get_potencia(self): return self.potencia
    def get_tac(self): return self.tac
    def get_tac_list(self): return self.tac_list
    def get_histerese(self): return self.histerese
    def get_frequencia(self): return self.frequencia
    def get_neighbours(self): return self.vizinhos
    def get_numero_ues_acampadas(self): return self.numero_ues_acampadas
    def get_noise_floor(self): return self.noise_floor
    

    # ==========================================
    # SETTERS 
    # ==========================================
    def set_x(self, novo_x): self.x = novo_x
    def set_y(self, novo_y): self.y = novo_y
    def set_altura_antena(self, nova_altura): self.altura_antena = nova_altura
    def set_ganho_antena_transmissao(self, novo_ganho): self.ganho_antena_transmissao = novo_ganho
    def set_potencia(self, nova_potencia): self.potencia = nova_potencia
    def set_histerese(self, nova_histerese): self.histerese = nova_histerese
    def set_frequencia(self, nova_frequencia): self.frequencia = nova_frequencia
    def set_tac(self, novo_tac): self.tac = novo_tac
    def set_tac_list(self, nova_tac_list): self.tac_list = nova_tac_list