import tkinter as tk
import config
import time
import queue

class GUI:
    def __init__(self, root, estation_list, fila_dados, fila_comandos):
        self.root = root
        self.estacoes = estation_list
        self.fila_dados = fila_dados
        self.fila_comandos = fila_comandos
        
        self.width = config.AREA_LARGURA
        self.height = config.AREA_ALTURA
        self.radius = config.UE_RAIO
        
        # Variáveis Visuais
        self.ids_triangulos = [] 
        self.ue0_canvas_id = None
        self.ue0_ttt_text_id = None # Id para o texto do cronômetro
        
        # Estados de Controle
        self.info_visivel = False
        self.pausado = False  
        self.tempo_simulacao = 0.0 
        
        self.ultimo_relogio_maquina = time.time()
        self.tempo_real_ativo = 0.0
        
        # Variáveis para o Log da UE 0
        self.ue0_ultimo_total_lu = 0     
        self.ue0_ultimo_total_handovers = 0  # Controle para log de handover
        self.ue0_ultima_estacao_conectada = None
        self.ue0_estava_em_ligacao = False

        # Memória da GUI para os status das estações
        self.status_estacoes = {'lu': [0]*len(self.estacoes), 'paging': [0]*len(self.estacoes)}

        self._setup_interface()
        self._criar_elementos()
        
        # Inicia o loop para escutar a simulação (Consumidor)
        self.escutar_simulacao()

    def _setup_interface(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.simulation_frame = tk.Frame(self.main_frame)
        self.simulation_frame.pack(side="left", padx=10, pady=10)

        self.chart_frame = tk.Frame(self.main_frame)
        self.chart_frame.pack(side="right", padx=10, pady=10, fill="y")

        self.canvas = tk.Canvas(self.simulation_frame, width=self.width, height=self.height, bg="white")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.ao_clicar_mouse)

        self.frame_relogios = tk.Frame(self.chart_frame, pady=5)
        self.frame_relogios.pack(anchor="nw")

        self.lbl_relogio_sim = tk.Label(self.frame_relogios, text="Simulation Time: 00:00:00", font=("Consolas", 11, "bold"), fg="blue")
        self.lbl_relogio_sim.pack(anchor="nw")

        self.lbl_relogio_real = tk.Label(self.frame_relogios, text="Real Time: 00:00:00", font=("Consolas", 10, "bold"), fg="green")
        self.lbl_relogio_real.pack(anchor="nw")
        
        self.title_ue = tk.Label(self.chart_frame, text="UE 0 Data", font=("Arial", 14, "bold"))
        self.title_ue.pack(anchor="nw", pady=(10, 0))

        # MODIFICADO: Label para exibir o Evento 3GPP ativo da UE 0 em tempo real
        self.lbl_ue0_evento = tk.Label(self.chart_frame, text="3GPP Event: Nenhum", font=("Arial", 10, "bold"), fg="#cc6600", anchor="w")
        self.lbl_ue0_evento.pack(anchor="nw", pady=(2, 10))

        self.labels_estacao = []
        for j in range(len(self.estacoes)):
            lbl = tk.Label(self.chart_frame, text="--", font=("Arial", 10), anchor="w")
            lbl.pack(anchor="nw")
            self.labels_estacao.append(lbl)

        lbl_log_title = tk.Label(self.chart_frame, text="Event log (UE 0):", font=("Arial", 9, "bold"), anchor="w", fg="#333")
        lbl_log_title.pack(anchor="nw", pady=(15, 0)) 

        self.log_text = tk.Text(self.chart_frame, height=10, width=35, font=("Consolas", 8))
        self.log_text.pack(anchor="nw", pady=(2, 10))

        self.botoes_frame = tk.Frame(self.chart_frame)
        self.botoes_frame.pack(anchor="nw", pady=(0, 10))

        self.btn_pause = tk.Button(self.botoes_frame, text="⏸ Pause", command=self.toggle_pause, width=10, bg="#ffcccc")
        self.btn_pause.pack(side="left", padx=(0, 5))

        self.btn_info = tk.Button(self.botoes_frame, text="▼ Information", command=self.toggle_info, width=12)
        self.btn_info.pack(side="left", padx=5)

        self.btn_call = tk.Button(self.botoes_frame, text="📞 Make Call", command=self.acionar_ligacao, width=12, bg="#add8e6")
        self.btn_call.pack(side="left", padx=5)
        
        self.info_frame = tk.Frame(self.chart_frame, bd=1, relief="solid")
        
        lbl_titulo_geral = tk.Label(self.info_frame, text="General information", font=("Arial", 10, "bold"), bg="#ddd", anchor="w")
        lbl_titulo_geral.pack(fill="x")
        
        self.lbl_global_total = tk.Label(self.info_frame, text="Total Location Updates (Todas UEs): 0", fg="purple", anchor="w")
        self.lbl_global_total.pack(anchor="w", padx=5, pady=5)

        self.lbl_global_paging = tk.Label(self.info_frame, text="Total Paging messages (Todas UEs): 0", fg="darkorange", anchor="w")
        self.lbl_global_paging.pack(anchor="w", padx=5, pady=2)

        # Label para Handovers Globais
        self.lbl_global_handover = tk.Label(self.info_frame, text="Total Handovers (Todas UEs): 0", fg="red", anchor="w")
        self.lbl_global_handover.pack(anchor="w", padx=5, pady=2)

        lbl_titulo_ue0 = tk.Label(self.info_frame, text="More information UE 0", font=("Arial", 10, "bold"), bg="#ddd", anchor="w")
        lbl_titulo_ue0.pack(fill="x", pady=(10, 0))

        self.lbl_ue0_tac = tk.Label(self.info_frame, text="Current TAC: -- | TAC List: --", fg="darkblue", font=("Arial", 9, "bold"), anchor="w")
        self.lbl_ue0_tac.pack(anchor="w", padx=5, pady=2)

        self.lbl_ue0_total = tk.Label(self.info_frame, text="Total Location Updates (UE 0): 0", fg="blue", anchor="w")
        self.lbl_ue0_total.pack(anchor="w", padx=5, pady=2)

        self.lbl_ue0_paging = tk.Label(self.info_frame, text="Total Paging messages: 0", fg="orange", anchor="w")
        self.lbl_ue0_paging.pack(anchor="w", padx=5, pady=2)
        
        # Label para Handovers da UE 0
        self.lbl_ue0_handover = tk.Label(self.info_frame, text="Total Handovers: 0", fg="red", anchor="w")
        self.lbl_ue0_handover.pack(anchor="w", padx=5, pady=2)

    def _criar_elementos(self):
        self.ids_triangulos = []
        self.ids_textos_contagem = []
        
        for i, est in enumerate(self.estacoes):
            s = config.ESTACAO_SIMBOLO_TAMANHO
            x, y = est.get_x(), est.get_y()
            
            tac_atual = est.get_tac()
            self.canvas.create_text(x, y - s - 12, text=f"TAC: {tac_atual}", font=("Arial", 8, "bold"), fill="#2b5797")
            
            tri_id = self.canvas.create_polygon(x, y-s, x-s, y+s, x+s, y+s, fill="green", outline="black")
            self.ids_triangulos.append(tri_id)
            self.canvas.create_text(x, y + s + 10, text=f"S{i+1}", font=("Arial", 9, "bold"), fill="black")
            
            txt_contagem_id = self.canvas.create_text(x, y + s + 22, text="0 UEs", font=("Arial", 8), fill="purple")
            self.ids_textos_contagem.append(txt_contagem_id)

        # Desenha apenas a UE 0
        self.ue0_canvas_id = self.canvas.create_oval(0, 0, 0, 0, fill="purple")
        
        # Cria o elemento de texto do cronômetro flutuante, inicialmente oculto
        self.ue0_ttt_text_id = self.canvas.create_text(0, 0, text="", font=("Arial", 9, "bold"), fill="darkorange", state="hidden")

    def toggle_info(self):
        if self.info_visivel:
            self.info_frame.pack_forget()
        else:
            self.info_frame.pack(anchor="nw", fill="x")
        self.info_visivel = not self.info_visivel

    def toggle_pause(self):
        self.pausado = not self.pausado
        self.fila_comandos.put({'comando': 'pausa', 'estado': self.pausado})
        
        if self.pausado:
            self.btn_pause.config(text="▶ Resume", bg="#ccffcc") 
        else:
            self.btn_pause.config(text="⏸ Pause", bg="#ffcccc") 
            self.ultimo_relogio_maquina = time.time()

    def acionar_ligacao(self):
        self.fila_comandos.put({'comando': 'ligacao'})

    def ao_clicar_mouse(self, event):
        if not self.pausado:
            self.fila_comandos.put({'comando': 'mover', 'x': event.x, 'y': event.y})

    def escutar_simulacao(self):
        if not self.pausado:
            agora = time.time()
            self.tempo_real_ativo += agora - self.ultimo_relogio_maquina
            self.ultimo_relogio_maquina = agora

        try:
            while True: 
                dados = self.fila_dados.get_nowait()
                
                if dados['tipo'] == 'ue_zero':
                    self.tempo_simulacao = dados['tempo']
                    self.atualizar_displays_relogio()
                    self._atualizar_visual_ue0(dados)
                    self._atualizar_tabela_ue0(dados)
                    self._atualizar_log_ue0(dados)
                    
                elif dados['tipo'] == 'estatisticas':
                    self.lbl_global_total.config(text=f"Total Location Updates (Todas UEs): {dados['global_lu']}")
                    self.lbl_global_paging.config(text=f"Total Paging messages (Todas UEs): {dados['global_paging']}")
                    self.lbl_global_handover.config(text=f"Total Handovers (Todas UEs): {dados.get('global_handover', 0)}")
                    
                    if 'lu_estacoes' in dados:
                        self.status_estacoes['lu'] = dados['lu_estacoes']
                        self.status_estacoes['paging'] = dados['paging_estacoes']
                   
                    if 'contagem_estacoes' in dados:
                        for i, qtd in enumerate(dados['contagem_estacoes']):
                            self.canvas.itemconfig(self.ids_textos_contagem[i], text=f"{qtd} UEs")
                   
        except queue.Empty:
            pass
            
        self.root.after(50, self.escutar_simulacao)

    def _atualizar_visual_ue0(self, dados):
        x, y = dados['x'], dados['y']
        r = self.radius
        
        # Atualiza posição e verifica TTT para mudar cor da UE
        ttt_inicio = dados.get('ttt_inicio')
        
        if ttt_inicio is not None:
            # Em estado de Time To Trigger: Fica laranja e mostra o tempo
            tempo_decorrido = self.tempo_simulacao - ttt_inicio
            self.canvas.itemconfig(self.ue0_canvas_id, fill="orange")
            
            # Posiciona o texto acima da UE e o deixa visível
            self.canvas.coords(self.ue0_ttt_text_id, x, y - r - 10)
            self.canvas.itemconfig(self.ue0_ttt_text_id, text=f"{tempo_decorrido:.1f}s", state="normal")
        else:
            # Estado Normal: Volta para roxo e esconde o texto
            self.canvas.itemconfig(self.ue0_canvas_id, fill="purple")
            self.canvas.itemconfig(self.ue0_ttt_text_id, state="hidden")

        self.canvas.coords(self.ue0_canvas_id, x-r, y-r, x+r, y+r)

        conectada_idx = dados['conectada_idx']
        candidato_idx = dados['melhor_idx']
        em_paging = dados['estacoes_em_paging_idx']
        piscar = False
        
        if dados['momento_paging'] is not None:
            tempo_desde_paging = self.tempo_simulacao - dados['momento_paging']
            if tempo_desde_paging < 2.0:
                piscar = (int(tempo_desde_paging * 5) % 2 == 0)

        for idx, tri_id in enumerate(self.ids_triangulos):
            cor = "green"
            if piscar and idx in em_paging:
                cor = "yellow"
            elif idx == conectada_idx:
                cor = "blue"
            elif idx == candidato_idx:
                cor = "red"
            self.canvas.itemconfig(tri_id, fill=cor)

    def _atualizar_tabela_ue0(self, dados):
        sinais = dados['sinais']
        dists = dados['distancias']
        conectada_idx = dados['conectada_idx']
        candidato_idx = dados['melhor_idx']
        vizinhas_idx = dados['vizinhas_idx']

        if sinais:
            for i, lbl in enumerate(self.labels_estacao):
                nf_atual = self.estacoes[i].get_noise_floor()
                
                lu_global_est = self.status_estacoes['lu'][i]
                pag_global_est = self.status_estacoes['paging'][i]
                info_extra = f" | LUs: {lu_global_est} | Pg: {pag_global_est}"

                if sinais[i] <= -999.0:
                    lbl.config(text=f"S{i+1} [NF: {nf_atual}]: --{info_extra}", fg="gray")
                    continue 

                cor = "black" 
                texto_viz = "" 
                
                if i == conectada_idx:
                    cor = "blue"
                    nomes_vizinhas = [f"S{v+1}" for v in vizinhas_idx]
                    if nomes_vizinhas:
                        texto_viz = f" | Viz: [{', '.join(nomes_vizinhas)}]"
                        
                elif i == candidato_idx:
                    cor = "red"
                    
                lbl.config(text=f"S{i+1} [NF: {nf_atual}]: {sinais[i]:.2f} dBm | {dists[i]:.3f} km{info_extra}{texto_viz}", fg=cor)

    def _atualizar_log_ue0(self, dados):
        # MODIFICADO: Captura e atualiza o evento 3GPP atual recebido do motor
        evento_atual = dados.get('evento_handover', "Nenhum")
        self.lbl_ue0_evento.config(text=f"Event: {evento_atual}")

        estacao_atual_idx = dados['conectada_idx']
        
        tac_atual = "--"
        tac_list = "--"
        if estacao_atual_idx is not None:
            tac_atual = self.estacoes[estacao_atual_idx].get_tac()
            tac_list = self.estacoes[estacao_atual_idx].get_tac_list()
            
        self.lbl_ue0_tac.config(text=f"Current TAC: {tac_atual} | TAC List: {tac_list}")

        total_atual = dados['total_lu']
        self.lbl_ue0_total.config(text=f"Total Location Updates (UE 0): {total_atual}")
        self.lbl_ue0_paging.config(text=f"Total Paging messages: {dados['total_pagings']}")
        
        total_handovers_atual = dados.get('total_handovers', 0)
        self.lbl_ue0_handover.config(text=f"Total Handovers: {total_handovers_atual}")

        if estacao_atual_idx is not None and estacao_atual_idx != self.ue0_ultima_estacao_conectada:
            self.log_text.insert(tk.END, f"[{self.tempo_simulacao:.1f}s] Conectado na Estação S{estacao_atual_idx + 1}\n")
            self.log_text.see(tk.END)
            self.ue0_ultima_estacao_conectada = estacao_atual_idx

        # Log de Location Update
        if total_atual > self.ue0_ultimo_total_lu:
            self.log_text.insert(tk.END, f"[{self.tempo_simulacao:.1f}s] LOCATION UPDATE (TAC: {tac_atual}) \n")
            self.log_text.see(tk.END)
            self.ue0_ultimo_total_lu = total_atual
            
        # Log de Handover
        if total_handovers_atual > self.ue0_ultimo_total_handovers:
            self.log_text.insert(tk.END, f"[{self.tempo_simulacao:.1f}s] HANDOVER CONCLUÍDO \n")
            self.log_text.see(tk.END)
            self.ue0_ultimo_total_handovers = total_handovers_atual
        
        em_ligacao = dados['em_ligacao']
        if em_ligacao and not self.ue0_estava_em_ligacao:
            self.log_text.insert(tk.END, f"[{self.tempo_simulacao:.1f}s] LIGAÇÃO INICIADA\n")
            self.log_text.see(tk.END)
            self.ue0_estava_em_ligacao = True
            self.btn_call.config(state="disabled", text="On call...", bg="#ccc")
            
        elif not em_ligacao and self.ue0_estava_em_ligacao:
            self.log_text.insert(tk.END, f"[{self.tempo_simulacao:.1f}s] LIGAÇÃO ENCERRADA\n")
            self.log_text.see(tk.END)
            self.ue0_estava_em_ligacao = False
            self.btn_call.config(state="normal", text="📞 Make Call", bg="#add8e6")

    def formatar_tempo(self, segundos):
        m, s = divmod(int(segundos), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def atualizar_displays_relogio(self):
        self.lbl_relogio_sim.config(text=f"Simulation Time: {self.formatar_tempo(self.tempo_simulacao)}")
        self.lbl_relogio_real.config(text=f"Real Time: {self.formatar_tempo(self.tempo_real_ativo)}")