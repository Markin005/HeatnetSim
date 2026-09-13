import random
import config

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
        self.estacao_conectada_idx = None 
        self.melhor_estacao_idx = None    
        self.sinais_atuais = []
        self.distancias_atuais = []
        self.total_location_updates = 0
        
        self.vizinhas_atuais = []
        
        # Variáveis de controle TAC
        self.tac_atual = "--" 
        self.lista_tac_registrada = []

        # Variáveis de Paging e Ligação
        self.em_ligacao = False
        self.tempo_fim_ligacao = 0  
        
        self.total_pagings = 0
        self.estacoes_em_paging = []
        self.momento_paging = None

        self.ultimo_segundo_verificado = -1
        
        # Modificado: 1 chance em 720 por segundo resulta em ~5 ligações por hora
        self.slot_chamada = random.randint(0, 719) 

        # Listas para rastrear eventos específicos por estação
        self.lu_estacoes = [0] * len(self.estacoes)
        self.paging_estacoes = [0] * len(self.estacoes)

        
        # Variáveis do Time To Trigger (TTT)
        self.ttt_segundos = 0.37
        self.ttt_inicio = None
        self.ttt_candidato_idx = None

        # Rastreamento do evento de Handover atual
        self.evento_handover_atual = "Nenhum"
        self.total_handovers = 0

    def location_update(self):
        pass 

    def executar_rodada(self, tempo_simulacao):
        # Encerra a ligação no tempo virtual
        if self.em_ligacao and tempo_simulacao >= self.tempo_fim_ligacao:
            self.em_ligacao = False
            # Se a ligação caiu, limpamos o cronômetro do TTT 
            self.ttt_inicio = None
            self.ttt_candidato_idx = None
            self.evento_handover_atual = "Nenhum"

        self._calcular_fisica_e_radio(tempo_simulacao)

        segundo_atual = int(tempo_simulacao)
        segundos_passados = segundo_atual - self.ultimo_segundo_verificado

        if segundos_passados > 0:
            for _ in range(segundos_passados):
                if not self.em_ligacao:
                    # Modificado: 1 chance em 720
                    valor_sorteado = random.randint(0, 719)
                    if valor_sorteado == self.slot_chamada:
                        self.fazer_ligacao(tempo_simulacao)
                        break 
            
            self.ultimo_segundo_verificado = segundo_atual

    def _calcular_fisica_e_radio(self, tempo_simulacao):
        self.movement.mover(self, config.AREA_LARGURA, config.AREA_ALTURA)

        self.sinais_atuais = [-1000.0] * len(self.estacoes)
        self.distancias_atuais = [0.0] * len(self.estacoes)
        
        estacoes_para_medir = []
        
        if self.estacao_conectada_idx is None:
            estacoes_para_medir = self.estacoes
            self.evento_handover_atual = "Nenhum (Desconectado)"
        else:
            estacao_atual = self.estacoes[self.estacao_conectada_idx]
            idx_atual = self.estacao_conectada_idx
            
            dist = self.movement.medir_distancia(self.x, self.y, estacao_atual.get_x(), estacao_atual.get_y())
            dist_km = max(dist / 1000, 0.001) 
            perda = self.model.medir_perda(estacao_atual.get_altura_antena(), dist_km, estacao_atual.get_frequencia())
            
            # SINAL PURO (Modelagem Okumura-Hata)
            potencia_puro = self.model.medir_sinal(
                estacao_atual.get_potencia(), estacao_atual.get_ganho_antena_transmissao(),
                self.ganho_antena, perda
            )
            
            # ADIÇÃO DO FADING: Aplica o desvanecimento usando a estação atual e o ID deste UE
            potencia_servidora = estacao_atual.aplicar_fading(potencia_puro, self.id)
            
            self.sinais_atuais[idx_atual] = potencia_servidora
            self.distancias_atuais[idx_atual] = dist_km

            # Identificação dos Eventos A1 e A2 baseados no Noise Floor
            if potencia_servidora < estacao_atual.get_noise_floor():
                estacoes_para_medir = self.vizinhas_atuais
                if self.em_ligacao:
                    self.evento_handover_atual = "A2"
                else:
                    self.evento_handover_atual = "Reselection"
            else:
                estacoes_para_medir = []
                self.melhor_estacao_idx = idx_atual
                if self.em_ligacao:
                    self.evento_handover_atual = "A1"
                else:
                    self.evento_handover_atual = "Idle (Sinal Bom)"
           
        for est in estacoes_para_medir:
            idx_real = self.estacoes.index(est)
            
            dist = self.movement.medir_distancia(self.x, self.y, est.get_x(), est.get_y())
            dist_km = max(dist / 1000, 0.001) 
            perda = self.model.medir_perda(est.get_altura_antena(), dist_km, est.get_frequencia())
            
            # SINAL PURO
            potencia_puro = self.model.medir_sinal(
                est.get_potencia(), est.get_ganho_antena_transmissao(),
                self.ganho_antena, perda
            )
            
            # ADIÇÃO DO FADING: Aplica o desvanecimento na medição da estação vizinha
            potencia = est.aplicar_fading(potencia_puro, self.id)
            
            self.sinais_atuais[idx_real] = potencia
            self.distancias_atuais[idx_real] = dist_km

        if self.sinais_atuais:
            self.melhor_estacao_idx = self.sinais_atuais.index(max(self.sinais_atuais))
            
            if self.estacao_conectada_idx is None:
                self.estacao_conectada_idx = self.melhor_estacao_idx
                
                estacao_servidora = self.estacoes[self.estacao_conectada_idx]
                self.tac_atual = estacao_servidora.get_tac()
                self.lista_tac_registrada = estacao_servidora.get_tac_list()
                
                self.estacoes[self.estacao_conectada_idx].incrementar_ue()
                self.reselection()
            
            elif self.melhor_estacao_idx != self.estacao_conectada_idx:
                potencia_acampada = self.sinais_atuais[self.estacao_conectada_idx]
                potencia_candidata = self.sinais_atuais[self.melhor_estacao_idx]
                histerese = self.estacoes[self.estacao_conectada_idx].histerese
                
                # A candidata superou a servidora + histerese?
                if (potencia_candidata - potencia_acampada) > histerese:
                    
                    if self.em_ligacao:
                        # Identificação do Evento A3
                        self.evento_handover_atual = f"A3 (S{self.melhor_estacao_idx+1} superou S{self.estacao_conectada_idx+1})"
                        
                        # Modo Handover (Aplica o Time To Trigger)
                        if self.ttt_candidato_idx != self.melhor_estacao_idx:
                            # Nova candidata superou a servidora agora: Inicia o cronômetro
                            self.ttt_candidato_idx = self.melhor_estacao_idx
                            self.ttt_inicio = tempo_simulacao
                            
                        elif (tempo_simulacao - self.ttt_inicio) >= self.ttt_segundos:
                            # O sinal ficou melhor durante todo o TTT: Realiza o Handover!
                            self._executar_troca_de_celula()
                    else:
                        # Modo Reselection (Idle): Troca imediata
                        self._executar_troca_de_celula()
                else:
                    # Se o sinal da candidata cair antes do tempo, cancela o Handover/TTT
                    self.ttt_inicio = None
                    self.ttt_candidato_idx = None
    
    def _executar_troca_de_celula(self):
        tac_antigo = self.estacoes[self.estacao_conectada_idx].get_tac()
        tac_novo = self.estacoes[self.melhor_estacao_idx].get_tac()
        lista_tac_antiga = self.estacoes[self.estacao_conectada_idx].get_tac_list()
        
        if tac_antigo != tac_novo:
            if tac_novo not in lista_tac_antiga:
                self.location_update()
                self.total_location_updates += 1
                self.lu_estacoes[self.melhor_estacao_idx] += 1
                
                self.lista_tac_registrada = self.estacoes[self.melhor_estacao_idx].get_tac_list()
            
            self.tac_atual = tac_novo
        
        self.estacoes[self.estacao_conectada_idx].decrementar_ue()
        self.estacao_conectada_idx = self.melhor_estacao_idx
        self.estacoes[self.estacao_conectada_idx].incrementar_ue()
        self.reselection()
        
        # Resetamos o TTT pois a troca foi efetuada com sucesso
        self.ttt_inicio = None
        self.ttt_candidato_idx = None
        if self.em_ligacao:
            self.total_handovers += 1
            self.evento_handover_atual = "A1"

    def fazer_ligacao(self, tempo_simulacao):
        if not self.em_ligacao:
            paginadas = []
            for i, est in enumerate(self.estacoes):
                if est.get_tac() in self.lista_tac_registrada:
                    est.paging() 
                    paginadas.append(est)
                    self.paging_estacoes[i] += 1
            
            self.estacoes_em_paging = paginadas
            self.total_pagings += len(paginadas) 
            self.momento_paging = tempo_simulacao 
            self.em_ligacao = True
            self.tempo_fim_ligacao = tempo_simulacao + 60
                    
    def reselection(self):
        if self.estacao_conectada_idx is not None:
            estacao_servidora = self.estacoes[self.estacao_conectada_idx]
            self.vizinhas_atuais = estacao_servidora.get_neighbours()
                    
    def get_x(self): return self.x
    def get_y(self): return self.y
    def get_sinais(self): return self.sinais_atuais
    def get_distancias(self): return self.distancias_atuais
    def get_melhor_estacao_idx(self): return self.melhor_estacao_idx
    def get_total_updates(self): return self.total_location_updates
    def get_vizinhas_atuais(self): return self.vizinhas_atuais
    def get_velocidade(self): return self.velocidade
    
    def set_x(self, x): self.x = x
    def set_y(self, y): self.y = y
    def set_destiny(self, d): self.destiny = d
    def get_destiny(self): return getattr(self, 'destiny', None)