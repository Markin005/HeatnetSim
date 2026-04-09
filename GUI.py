import tkinter as tk
import config
import time

class GUI:
    def __init__(self, root, ue_list, estation_list):
        self.root = root
        self.ues = ue_list
        self.estacoes = estation_list
        
        self.width = config.AREA_LARGURA
        self.height = config.AREA_ALTURA
        self.radius = config.UE_RAIO
        
        # CONFIGURAÇÃO DE VISIBILIDADE
        qtd_visiveis = 1
        self.ues_visiveis = self.ues[:qtd_visiveis] 
        self.ue_foco_dados = self.ues[0] # UE 0 (Roxa)

        # Mapeamentos Visuais
        self.mapa_ue_canvas = {} 
        self.ids_triangulos = [] 

        # ESTADOS DE CONTROLE
        self.idx_estacao_vermelha = None
        self.info_visivel = False
        self.pausado = False  
        
        # Variáveis para o Log da UE 0
        self.tempo_simulacao = 0.0       
        self.ue0_ultimo_total_lu = 0     
        self.ue0_ultima_estacao_conectada = None
        self.ue0_estava_em_ligacao = False

        self._setup_interface()
        self._criar_elementos()
        
        self.clock_simulacao()

    def _setup_interface(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.simulation_frame = tk.Frame(self.main_frame)
        self.simulation_frame.pack(side="left", padx=10, pady=10)

        self.chart_frame = tk.Frame(self.main_frame)
        self.chart_frame.pack(side="right", padx=10, pady=10, fill="y")

        self.canvas = tk.Canvas(
            self.simulation_frame, width=self.width, height=self.height, bg="white"
        )
        self.canvas.pack()

        # BARRA LATERAL 
        self.title_ue = tk.Label(self.chart_frame, text=f"UE {self.ue_foco_dados.id} Data", font=("Arial", 14, "bold"))
        self.title_ue.pack(anchor="nw")

        # Tabela de Estações
        self.labels_estacao = []
        for j in range(len(self.estacoes)):
            lbl = tk.Label(self.chart_frame, text="--", font=("Arial", 10), anchor="w")
            lbl.pack(anchor="nw")
            self.labels_estacao.append(lbl)

        # LOG DE EVENTOS FIXO (Logo abaixo da tabela)
        lbl_log_title = tk.Label(self.chart_frame, text="Event log (UE 0):", font=("Arial", 9, "bold"), anchor="w", fg="#333")
        lbl_log_title.pack(anchor="nw", pady=(15, 0)) # Margem em cima para separar da tabela

        self.log_text = tk.Text(self.chart_frame, height=10, width=35, font=("Consolas", 8))
        self.log_text.pack(anchor="nw", pady=(2, 10))

        # BOTÕES DE CONTROLE
        self.botoes_frame = tk.Frame(self.chart_frame)
        self.botoes_frame.pack(anchor="nw", pady=(0, 10))

        # Botão PAUSE
        self.btn_pause = tk.Button(self.botoes_frame, text="⏸ Pause", command=self.toggle_pause, width=10, bg="#ffcccc")
        self.btn_pause.pack(side="left", padx=(0, 5))

        # Botão INFO
        self.btn_info = tk.Button(self.botoes_frame, text="▼ Information", command=self.toggle_info, width=12)
        self.btn_info.pack(side="left", padx=5)

        #nBotão FAZER LIGAÇÃO
        self.btn_call = tk.Button(self.botoes_frame, text="📞 Make Call", command=self.acionar_ligacao, width=12, bg="#add8e6")
        self.btn_call.pack(side="left", padx=5)
        
        # ÁREA DE INFO OCULTA
        self.info_frame = tk.Frame(self.chart_frame, bd=1, relief="solid")
        
        # INFORMAÇÕES GERAIS
        lbl_titulo_geral = tk.Label(self.info_frame, text="General information", font=("Arial", 10, "bold"), bg="#ddd", anchor="w")
        lbl_titulo_geral.pack(fill="x")
        
        self.lbl_global_total = tk.Label(self.info_frame, text="Total Location Updates (Todas UEs): 0", fg="purple", anchor="w")
        self.lbl_global_total.pack(anchor="w", padx=5, pady=5)

       
        # SEÇÃO 2 (INFORMAÇÕES UE 0)
        lbl_titulo_ue0 = tk.Label(self.info_frame, text=f"More information UE {self.ue_foco_dados.id}", font=("Arial", 10, "bold"), bg="#ddd", anchor="w")
        lbl_titulo_ue0.pack(fill="x", pady=(10, 0))

        self.lbl_ue0_la = tk.Label(self.info_frame, text="Location Area in the moment: --", fg="darkblue", font=("Arial", 9, "bold"), anchor="w")
        self.lbl_ue0_la.pack(anchor="w", padx=5, pady=2)

        self.lbl_ue0_total = tk.Label(self.info_frame, text="Total Location Updates (UE 0): 0", fg="blue", anchor="w")
        self.lbl_ue0_total.pack(anchor="w", padx=5, pady=2)

        # NOVO: Label para contar os Pagings
        self.lbl_ue0_paging = tk.Label(self.info_frame, text="Total Paging messages: 0", fg="orange", anchor="w")
        self.lbl_ue0_paging.pack(anchor="w", padx=5, pady=2)

    def _criar_elementos(self):
        self.ids_triangulos = []
        self.ids_textos_contagem = []
        
        # Usa o enumerate para saber o número da estação (0, 1, 2...)
        for i, est in enumerate(self.estacoes):
            
            # Coordenadas e tamanho do símbolo
            s = config.ESTACAO_SIMBOLO_TAMANHO
            x, y = est.get_x(), est.get_y()
            
            # Desenha o triângulo da estação
            tri_id = self.canvas.create_polygon(x, y-s, x-s, y+s, x+s, y+s, fill="green", outline="black")
            self.ids_triangulos.append(tri_id)

            self.canvas.create_text(x, y + s + 10, text=f"S{i+1}", font=("Arial", 9, "bold"), fill="black")

            txt_contagem_id = self.canvas.create_text(x, y + s + 22, text="0 UEs", font=("Arial", 8), fill="purple")
            self.ids_textos_contagem.append(txt_contagem_id)

        for ue in self.ues:
            state = "normal" if ue in self.ues_visiveis else "hidden"
            cor = "purple" if ue.id == 0 else "blue"
            cid = self.canvas.create_oval(0, 0, 0, 0, fill=cor, state=state)
            self.mapa_ue_canvas[ue] = cid

    
    # CONTROLES DE INTERFACE
    def toggle_info(self):
        if self.info_visivel:
            self.info_frame.pack_forget()
        else:
            self.info_frame.pack(anchor="nw", fill="x")
        self.info_visivel = not self.info_visivel

    def toggle_pause(self):
        self.pausado = not self.pausado
        if self.pausado:
            self.btn_pause.config(text="▶ Resume", bg="#ccffcc") 
        else:
            self.btn_pause.config(text="⏸ Pause", bg="#ffcccc") 
    
    def acionar_ligacao(self):
        # LIgacao UE 0
        self.ue_foco_dados.fazer_ligacao()

    # ATUALIZAÇÕES VISUAIS
    def _atualizar_cor_triangulo(self, ue): 
        conectada_idx = ue.estacao_conectada_idx
        candidato_idx = ue.melhor_estacao_idx
        
        # Lógica do Pisca-Pisca do Paging
        piscar_amarelo = False
        if hasattr(ue, 'momento_paging') and ue.momento_paging is not None:
            tempo_desde_paging = time.time() - ue.momento_paging
            
            if tempo_desde_paging < 2.0: # Fica a piscar durante 2 segundos
                # Alterna entre True e False a cada 0.2 segundos (cria o efeito de piscar)
                piscar_amarelo = (int(tempo_desde_paging * 5) % 2 == 0)
            else:
                # O tempo acabou, limpa as variáveis
                ue.momento_paging = None
                ue.estacoes_em_paging = []

        # Aplicação das Cores
        for idx, tri_id in enumerate(self.ids_triangulos):
            estacao = self.estacoes[idx]
            cor = "green" # Padrão
            
            # Se está na hora de piscar E a antena faz parte das que enviaram Paging
            if piscar_amarelo and estacao in getattr(ue, 'estacoes_em_paging', []):
                cor = "yellow"
            elif idx == conectada_idx:
                cor = "blue"
            elif idx == candidato_idx:
                cor = "red"
                
            self.canvas.itemconfig(tri_id, fill=cor)

    def _atualizar_log_ue0(self, ue):
        try:
            la_atual = ue.la_atual 
        except AttributeError:
            la_atual = "--"

        self.lbl_ue0_la.config(text=f"Location Area in the moment: {la_atual}")

        total_atual = ue.get_total_updates()
        self.lbl_ue0_total.config(text=f"Total Location Updates (UE 0): {total_atual}")

        
        # VERIFICA CONEXÃO
        estacao_atual_idx = getattr(ue, 'estacao_conectada_idx', None)
        
        # Se a estação conectada for diferente da última que a GUI lembrava
        if estacao_atual_idx is not None and estacao_atual_idx != self.ue0_ultima_estacao_conectada:
            mensagem = f"[{self.tempo_simulacao:.1f}s] Conectado na Estação S{estacao_atual_idx + 1}\n"
            self.log_text.insert(tk.END, mensagem)
            self.log_text.see(tk.END)
            
            # Atualiza a memória da GUI
            self.ue0_ultima_estacao_conectada = estacao_atual_idx

        
        # VERIFICA LOCATION UPDATE 
        if total_atual > self.ue0_ultimo_total_lu:
            mensagem = f"[{self.tempo_simulacao:.1f}s] LOCATION UPDATE (LA: {la_atual}) \n"
            self.log_text.insert(tk.END, mensagem)
            self.log_text.see(tk.END)
            
            self.ue0_ultimo_total_lu = total_atual
        
        # VERIFICA STATUS DA LIGAÇÃO 
        if ue.em_ligacao and not self.ue0_estava_em_ligacao:
            # Ligação acabou de começar
            mensagem = f"[{self.tempo_simulacao:.1f}s] LIGAÇÃO INICIADA (10s)\n"
            self.log_text.insert(tk.END, mensagem)
            self.log_text.see(tk.END)
            self.ue0_estava_em_ligacao = True
            
            # Muda visual do botão
            self.btn_call.config(state="disabled", text="On call...", bg="#ccc")
            
        elif not ue.em_ligacao and self.ue0_estava_em_ligacao:
            # Ligação acabou de terminar
            mensagem = f"[{self.tempo_simulacao:.1f}s] LIGAÇÃO ENCERRADA\n"
            self.log_text.insert(tk.END, mensagem)
            self.log_text.see(tk.END)
            self.ue0_estava_em_ligacao = False
            
            # Restaura o botão
            self.btn_call.config(state="normal", text="📞 Make Call", bg="#add8e6")
        
        total_pagings = getattr(ue, 'total_pagings', 0)
        self.lbl_ue0_paging.config(text=f"Total Paging messages: {total_pagings}")

    def _atualizar_tabela(self, ue):
        sinais = ue.get_sinais()
        dists = ue.get_distancias()
        
        # Pega as duas estações importantes
        conectada_idx = getattr(ue, 'estacao_conectada_idx', None)
        candidato_idx = getattr(ue, 'melhor_estacao_idx', None)
        
        if sinais:
            for i, lbl in enumerate(self.labels_estacao):
                
                # Busca o Noise Floor da estação atual do loop
                nf_atual = self.estacoes[i].get_noise_floor()
                
                if sinais[i] <= -999.0:
                    # Deixa cinza
                    lbl.config(text=f"S{i+1} [NF: {nf_atual}]: --", fg="gray")
                    continue 
                

                cor = "black" # Cor padrão para antenas medidas
                texto_viz = "" 
                
                # Aplica as cores na tabela
                if i == conectada_idx:
                    cor = "blue"
                    nomes_vizinhas = []
                    vizinhas_da_ue = ue.get_vizinhas_atuais() 
                    
                    if vizinhas_da_ue:
                        for vizinho in vizinhas_da_ue:
                            numero_vizinho = self.estacoes.index(vizinho) + 1
                            nomes_vizinhas.append(f"S{numero_vizinho}")
                    
                        texto_viz = f" | Viz: [{', '.join(nomes_vizinhas)}]"
                        
                elif i == candidato_idx:
                    cor = "red"
                    
                # Imprime os dados reais 
                lbl.config(text=f"S{i+1} [NF: {nf_atual}]: {sinais[i]:.2f} dBm | {dists[i]:.3f} km{texto_viz}", fg=cor)

    def receber_ordem_de_desenho(self, ue_obj):
        canvas_id = self.mapa_ue_canvas[ue_obj]

        if ue_obj in self.ues_visiveis:
            x, y = ue_obj.get_x(), ue_obj.get_y()
            r = self.radius
            self.canvas.coords(canvas_id, x-r, y-r, x+r, y+r)
            self.canvas.itemconfig(canvas_id, state="normal")
        else:
            self.canvas.itemconfig(canvas_id, state="hidden")

        if ue_obj == self.ue_foco_dados:
            self._atualizar_tabela(ue_obj)
            
           
            self._atualizar_cor_triangulo(ue_obj)
            
            self._atualizar_log_ue0(ue_obj)

   
    def clock_simulacao(self):
        if not self.pausado:
            total_global = 0
            
            for ue in self.ues:
                ue.executar_rodada() 
                total_global += ue.get_total_updates()
            
            self.lbl_global_total.config(text=f"Total Location Updates (Todas UEs): {total_global}")
            
            
            for i, est in enumerate(self.estacoes):
                try:
                    
                    qtd = est.get_numero_ues_acampadas() 
                except AttributeError:
                    qtd = 0 
                    
                txt_id = self.ids_textos_contagem[i]
                self.canvas.itemconfig(txt_id, text=f"{qtd} UEs")
            
            self.tempo_simulacao += 0.1
        
        self.root.after(100, self.clock_simulacao)