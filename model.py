class model:
    def __init__(self,):
        pass

    def medir_sinal(self, potencia_transmitida, ganho_transmissao, ganho_recepcao,perda):
        potencia_recebida = potencia_transmitida + ganho_transmissao + ganho_recepcao - perda
        return potencia_recebida
    