import math
from model import model
import config

class okumura_hata(model):
    def __init__(self):
        pass

   
    def medir_perda(self, altura_antena_estacao, distancia, frequencia): 
        
        altura_antena_movel = config.ALTURA_ANTENA_MOVEL
        
        # Fórmula de Okumura-Hata (para áreas urbanas)
        # Pu = 69.55 + 26.16 * log10(f) - 13.82 * log10(hb) - a(hm) + (44.9 - 6.55 * log10(hb)) * log10(d)
        a_hm = self.fator_correcao(frequencia, altura_antena_movel)
        Pu = 69.55 + 26.16 * math.log10(frequencia) - 13.82 * math.log10(altura_antena_estacao) - a_hm + (44.9 - 6.55 * math.log10(altura_antena_estacao)) * math.log10(distancia)
        return Pu
    
    def fator_correcao(self, frequencia, altura_antena_movel):
        # Formula para cidades de pequeno a medio porte
        # a(hm) = (1.1*log10(f) - 0.7)*hm - (1.56*log10(f) - 0.8)
        return (1.1 * math.log10(frequencia) - 0.7) * altura_antena_movel - (1.56 * math.log10(frequencia) - 0.8)