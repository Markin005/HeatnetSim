import tkinter as tk
import GUI
import ue
import estation
import okumura_hata
import random_way_point
import mouse_movement
import config
import time
import resource




# LOOP PRINCIPAL DA SIMULAÇÃO
def clock_simulacao(root, app, list_ue, estation_list):
    # Calcula exatamente quanto tempo físico (real) passou desde o último frame
    agora = time.time()
    passo_real_de_tempo = agora - app.ultimo_relogio_maquina
    app.ultimo_relogio_maquina = agora  # Atualiza a marcação para o próximo giro

    if not app.pausado:
        # 1. O Mundo Virtual avança puramente pela matemática (o Quantum)
        app.tempo_simulacao += config.DELTA_T
        
        # 2. O Mundo Real soma apenas o tempo físico que o PC gastou
        app.tempo_real_ativo += passo_real_de_tempo
        
        app.atualizar_displays_relogio()

        total_global = 0
        
        # Executa a rodada (Física e Rádio) para todas as UEs
        for uma_ue in list_ue:
            uma_ue.executar_rodada(app.tempo_simulacao) 
            total_global += uma_ue.get_total_updates()
        
        # Atualiza a contagem total de Location Updates na tela
        app.lbl_global_total.config(text=f"Total Location Updates (Todas UEs): {total_global}")
        
        # Atualiza o texto de quantas UEs estão acampadas em cada estação
        for i, est in enumerate(estation_list):
            try:
                qtd = est.get_numero_ues_acampadas() 
            except AttributeError:
                qtd = 0 
                
            txt_id = app.ids_textos_contagem[i]
            app.canvas.itemconfig(txt_id, text=f"{qtd} UEs")
    
    # Chama a próxima rodada
    root.after(config.TICK_TKINTER_MS, clock_simulacao, root, app, list_ue, estation_list)


def gerar_relatorio(app, list_ue):
    qtd_ue = len(list_ue)
    tempo_real = app.tempo_real_ativo    # Tempo do seu relógio de pulso
    tempo_virtual = app.tempo_simulacao  # Tempo que passou dentro da Matrix
    quantum = config.DELTA_T             # Puxa o valor do Quantum usado na simulação

    # ==========================================
    # CÁLCULO DE MEMÓRIA (Nativo Linux)
    # ==========================================
    # O ru_maxrss pega o "Pico" de memória (Resident Set Size) usado pelo simulador.
    # ATENÇÃO: No Linux, o resource devolve esse valor em Kilobytes (KB).
    memoria_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    memoria_mb = memoria_kb / 1024.0 # Converte de KB para MB

    nome_arquivo = f"tempo_simulacao_{qtd_ue}_ues.txt"

    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("====================================================\n")
        f.write("         RELATÓRIO DE TEMPO E RECURSOS              \n")
        f.write("====================================================\n")
        f.write(f"Quantidade de UEs:          {qtd_ue}\n")
        f.write(f"Quantum:          {quantum} segundos/rodada\n")
        f.write(f"Tempo Virtual Processado:   {tempo_virtual:.2f} segundos\n")
        f.write(f"Tempo Real Decorrido:       {tempo_real:.2f} segundos\n")
        f.write(f"Pico de Memória RAM (top):  {memoria_mb:.2f} MB\n")
        f.write("----------------------------------------------------\n")
        
        # Cálculo de Eficiência
        if tempo_real > 0:
            fator = tempo_virtual / tempo_real
            f.write(f"Velocidade do Motor:        {fator:.2f}x mais rápido que o tempo real\n")
        
        f.write("====================================================\n")

    print(f"\n[INFO] Relatório de tempos salvo: {nome_arquivo}")



if __name__ == "__main__":
    root = tk.Tk()
    root.title("Simulador de Handover e Location Update")

    
    # 1. Modelos
    movimento_aleatorio = random_way_point.random_waypoint() # Para as UEs normais
    movimento_mouse = mouse_movement.mouse_movement()        # Para a UE 0
    model = okumura_hata.okumura_hata()

    
    # 2. Estações 
    estation_list = []
    for est_config_dict in config.ESTACOES_CONFIG:
        estation_list.append(estation.estation(est_config_dict))
   
    # Cada estação procura suas vizinhas
    for est in estation_list:
        est.calcular_estacoes_vizinhas(estation_list)

    
    # 3. UEs 
    list_ue = []
    for i in range(config.quantidade_ue):
        if i == 0:
            # A UE 0 (sua bolinha roxa) recebe o motor controlado pelo mouse
            list_ue.append(ue.ue(i, movimento_mouse, model, estation_list))
        else:
            # Todas as outras (bolinhas azuis) recebem o motor aleatório
            list_ue.append(ue.ue(i, movimento_aleatorio, model, estation_list))

    
    # 4. Interface Gráfica (GUI)
    app = GUI.GUI(root, list_ue, estation_list)

    # Conexão entre GUI e UE para atualização visual
    for uma_ue in list_ue:
        uma_ue.registrar_callback_visual(app.receber_ordem_de_desenho)

    def fechar_e_salvar():
        gerar_relatorio(app, list_ue)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", fechar_e_salvar)

   
    # 5. Start do Relógio e da Interface
    clock_simulacao(root, app, list_ue, estation_list)
    
    # Inicia a interface gráfica
    root.mainloop()