import random
import config
import threading
import time

class ue:
    def __init__(self, id_ue, movement_obj, model_obj, estacoes_list):
        self.id = id_ue
        self.movement = movement_obj
        self.model = model_obj
        self.estacoes = estacoes_list
        
        self.x = random.randint(0, config.AREA_LARGURA)
        self.y = random.randint(0, config.AREA_ALTURA)
        self.velocidade = config.UE_VELOCIDADE
        self.ganho_antena = config.GANHO_ANTENA_RECEPCAO
        
        # Estados 
        self.estacao_conectada_idx = None # Célula Servidora (Acampada - Azul)
        self.melhor_estacao_idx = None    # Célula Candidata (Vermelha)
        self.sinais_atuais = []
        self.distancias_atuais = []
        self.total_location_updates = 0
        self.em_ligacao = False

        self.vizinhas_atuais = []
        
        self.la_atual = "--" 
        self.funcao_atualizar_tela = None

        # Variáveis de Paging
        self.total_pagings = 0
        self.estacoes_em_paging = []
        self.momento_paging = None

        self.ultimo_segundo_verificado = -1
        self.slot_chamada = random.randint(0, 359) # 10 chamdas em uma 1 horas = 1 chamadada em 6 minutos(360)
      

    def location_update(self):
        pass

    def registrar_callback_visual(self, funcao):
        self.funcao_atualizar_tela = funcao

    def executar_rodada(self, tempo_simulacao):
        self._calcular_fisica_e_radio()

        segundo_atual = int(tempo_simulacao)
        segundos_passados = segundo_atual - self.ultimo_segundo_verificado

        if segundos_passados > 0:
            for _ in range(segundos_passados):
                if not self.em_ligacao:
                    valor_sorteado = random.randint(0, 359)
                    
                    if valor_sorteado == self.slot_chamada:
                        self.fazer_ligacao()
                        break 
            
            self.ultimo_segundo_verificado = segundo_atual

        if self.funcao_atualizar_tela:
            self.funcao_atualizar_tela(self)

    def _calcular_fisica_e_radio(self):
        self.movement.mover(self, config.AREA_LARGURA, config.AREA_ALTURA)

        # 1. Preenche a lista com sinais "mortos" (-1000 dBm) 
        self.sinais_atuais = [-1000.0] * len(self.estacoes)
        self.distancias_atuais = [0.0] * len(self.estacoes)
        
        estacoes_para_medir = []
        
        # 2. Lógica de medição baseada no Threshold (Noise Floor)
        if self.estacao_conectada_idx is None:
            # INITIAL CELL SELECTION: Mede todas para achar a primeira
            estacoes_para_medir = self.estacoes
            
        else:
            # CELL RESELECTION: Mede a antena conectada PRIMEIRO
            estacao_atual = self.estacoes[self.estacao_conectada_idx]
            idx_atual = self.estacao_conectada_idx
            
            # Faz a matemática da servidora
            dist = self.movement.medir_distancia(self.x, self.y, estacao_atual.get_x(), estacao_atual.get_y())
            dist_km = max(dist / 1000, 0.001) 
            perda = self.model.medir_perda(estacao_atual.get_altura_antena(), dist_km, estacao_atual.get_frequencia())
            potencia_servidora = self.model.medir_sinal(
                estacao_atual.get_potencia(), estacao_atual.get_ganho_antena_transmissao(),
                self.ganho_antena, perda
            )
            
            # Guarda o sinal atual
            self.sinais_atuais[idx_atual] = potencia_servidora
            self.distancias_atuais[idx_atual] = dist_km

            
            # NOVO: VERIFICA O NOISE FLOOR PARA DECIDIR SE MEDE VIZINHAS
            if potencia_servidora < estacao_atual.get_noise_floor():
                # Sinal está ruim
                estacoes_para_medir = self.vizinhas_atuais
            else:
                # Sinal está bom - lista de medição vazia 
                estacoes_para_medir = []
                # Como não vai medir mais ninguém, a melhor estação continua sendo a atual
                self.melhor_estacao_idx = idx_atual
           

        
        # (Se o sinal estiver bom, essa lista estará vazia e o loop nem roda
        for est in estacoes_para_medir:
            idx_real = self.estacoes.index(est)
            
            dist = self.movement.medir_distancia(self.x, self.y, est.get_x(), est.get_y())
            dist_km = max(dist / 1000, 0.001) 
            perda = self.model.medir_perda(est.get_altura_antena(), dist_km, est.get_frequencia())
            potencia = self.model.medir_sinal(
                est.get_potencia(), est.get_ganho_antena_transmissao(),
                self.ganho_antena, perda
            )
            
            self.sinais_atuais[idx_real] = potencia
            self.distancias_atuais[idx_real] = dist_km

        if self.sinais_atuais:
            self.melhor_estacao_idx = self.sinais_atuais.index(max(self.sinais_atuais))
            
            # INITIAL CELL SELECTION Se não está acampada em nenhuma, acampa na melhor
            if self.estacao_conectada_idx is None:
                self.estacao_conectada_idx = self.melhor_estacao_idx
                self.la_atual = self.estacoes[self.estacao_conectada_idx].get_location_area()

                #Entra estacao
                self.estacoes[self.estacao_conectada_idx].incrementar_ue()
                
                # Gatilho inicial
                self.reselection()
            
            # Se a candidata (Vermelha) é diferente da acampada (Azul)
            elif self.melhor_estacao_idx != self.estacao_conectada_idx:
                potencia_acampada = self.sinais_atuais[self.estacao_conectada_idx]
                potencia_candidata = self.sinais_atuais[self.melhor_estacao_idx]
                histerese = self.estacoes[self.estacao_conectada_idx].histerese
                
                # CELL RESELECTION: A condição de resseleção (com histerese) foi atingida?
                if (potencia_candidata - potencia_acampada) > histerese:
                    area_antiga = self.estacoes[self.estacao_conectada_idx].get_location_area()
                    area_nova = self.estacoes[self.melhor_estacao_idx].get_location_area()
                    
                    if area_antiga != area_nova:
                        self.location_update()
                        self.total_location_updates += 1
                        self.la_atual = area_nova
                    
                    # SAI DA ESTAÇÃO
                    self.estacoes[self.estacao_conectada_idx].decrementar_ue()

                    # Efetiva a troca da célula servidora
                    self.estacao_conectada_idx = self.melhor_estacao_idx

                    self.estacoes[self.estacao_conectada_idx].incrementar_ue()
                    
                   
                    self.reselection()
    
    def fazer_ligacao(self):
        #Inicia uma chamada e dispara o Paging na rede.
        if not self.em_ligacao:
            # 1. DISPARA O PAGING NA LOCATION AREA ATUAL
            paginadas = []
            for est in self.estacoes:
                if est.get_location_area() == self.la_atual:
                    est.paging() # Chama a função 
                    paginadas.append(est)
            
            # Guarda as informações para a GUI poder piscar as antenas e contar
            self.estacoes_em_paging = paginadas
            self.total_pagings += len(paginadas) # Soma 1 para cada antena que fez o paging
            self.momento_paging = time.time() # Marca o tempo para o pisca-pisca
            
            # 2. INICIA A LIGAÇÃO
            threading.Thread(target=self._rotina_ligacao, daemon=True).start()

    def _rotina_ligacao(self):
        self.em_ligacao = True
        
        # Fica 5 segundos "em ligação"
        time.sleep(5) 
        
        self.em_ligacao = False
                    
    
    # LÓGICA DE RESELECTION
    def reselection(self):
        # Garante que a UE está acampada em alguma estação
        if self.estacao_conectada_idx is not None:
            estacao_servidora = self.estacoes[self.estacao_conectada_idx]
            # A UE recebe e guarda a lista de vizinhas
            self.vizinhas_atuais = estacao_servidora.get_neighbours()

            
                    
    
    # Getters e Setters
    def get_x(self): return self.x
    def get_y(self): return self.y
    def get_sinais(self): return self.sinais_atuais
    def get_distancias(self): return self.distancias_atuais
    def get_melhor_estacao_idx(self): return self.melhor_estacao_idx
    def get_total_updates(self): return self.total_location_updates
    def get_vizinhas_atuais(self): return self.vizinhas_atuais
    
    def set_x(self, x): self.x = x
    def set_y(self, y): self.y = y
    def set_destiny(self, d): self.destiny = d
    def get_destiny(self): return getattr(self, 'destiny', None)
    def get_velocidade(self): return self.velocidade