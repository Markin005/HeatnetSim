import tkinter as tk
import GUI
import ue
import estation
import okumura_hata
import random_way_point
import mouse_movement
import config
import time
import threading
import sys
import math
import queue
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import itertools 
import random
import statistics 
import os 

# FUNÇÃO AUXILIAR PARA MODA
def moda_segura(dados):
    """Retorna a moda de forma segura, evitando erros se houver empates."""
    if not dados:
        return 0
    try:
        return statistics.mode(dados)
    except statistics.StatisticsError:
        from collections import Counter
        c = Counter(dados)
        return c.most_common(1)[0][0]

# GERAÇÃO DINÂMICA DE POSIÇÕES
def gerar_posicoes_estacoes(num_estacoes, largura, altura, margem=30, dist_minima=120):
    """
    Gera posições aleatórias para as estações, garantindo espaçamento 
    mínimo e mantendo-as dentro do mapa (descontando a margem).
    """
    posicoes = []
    tentativas_maximas = 1000
    
    for _ in range(num_estacoes):
        valida = False
        tentativas = 0
        x, y = 0, 0
        
        while not valida and tentativas < tentativas_maximas:
            # Sorteia dentro da área útil (descontando a margem para não encostar na borda)
            x = random.randint(margem, largura - margem)
            y = random.randint(margem, altura - margem)
            
            # Verifica a distância com todas as estações já posicionadas
            conflito = False
            for px, py in posicoes:
                dist = math.dist((x, y), (px, py))
                if dist < dist_minima:
                    conflito = True
                    break
            
            if not conflito:
                posicoes.append((x, y))
                valida = True
            
            tentativas += 1
            
        # Se esgotar as tentativas, adiciona a última gerada e avisa
        if not valida:
            print(f"[AVISO] Dificuldade para espaçar as estações. O espaçamento pode ser menor que {dist_minima}m.")
            posicoes.append((x, y))
            
    return posicoes


# FUNÇÃO DO MULTIPROCESSING
def run_ue_chunk(ue_chunk, stop_event, delta_t, fila_dados, fila_comandos, chunk_id, usar_interface, tempo_max):
    tempo_simulacao = 0.0
    contador_gui = 0
    pausado = False
    
    ue_zero = next((u for u in ue_chunk if u.id == 0), None)

    while not stop_event.is_set():
        if usar_interface:
            try:
                while True:
                    cmd = fila_comandos.get_nowait()
                    if cmd['comando'] == 'pausa':
                        pausado = cmd['estado']
                    elif cmd['comando'] == 'mover' and ue_zero:
                        ue_zero.set_destiny((cmd['x'], cmd['y']))
                    elif cmd['comando'] == 'ligacao' and ue_zero:
                        ue_zero.fazer_ligacao(tempo_simulacao)
            except queue.Empty:
                pass

            if pausado:
                time.sleep(0.1)
                continue

        tempo_simulacao += delta_t
        
        # Condição de parada por tempo virtual (Apenas Modo Terminal)
        if not usar_interface and tempo_simulacao >= tempo_max:
            break

        num_estacoes = len(ue_chunk[0].estacoes)
        contagem_local = [0] * num_estacoes
        
        # Contadores por estação locais deste núcleo
        lu_por_estacao_local = [0] * num_estacoes
        paging_por_estacao_local = [0] * num_estacoes
        
        soma_lu_local = 0
        soma_paging_local = 0
        soma_handover_local = 0

        for uma_ue in ue_chunk:
            uma_ue.executar_rodada(tempo_simulacao)
            idx = getattr(uma_ue, 'estacao_conectada_idx', None)
            if idx is not None:
                contagem_local[idx] += 1
                
            # Coleta individual do histórico de cada estação dentro da UE
            for i in range(num_estacoes):
                lu_por_estacao_local[i] += uma_ue.lu_estacoes[i]
                paging_por_estacao_local[i] += uma_ue.paging_estacoes[i]
                
            soma_lu_local += uma_ue.get_total_updates()
            soma_paging_local += getattr(uma_ue, 'total_pagings', 0)
            soma_handover_local += getattr(uma_ue, 'total_handovers', 0)
        
        if usar_interface:
            contador_gui += 1
            if contador_gui >= 10:
                contador_gui = 0
                if ue_zero:
                    vizinhas_idx = [ue_zero.estacoes.index(v) for v in getattr(ue_zero, 'vizinhas_atuais', [])]
                    paging_idx = [ue_zero.estacoes.index(p) for p in getattr(ue_zero, 'estacoes_em_paging', [])]

                    dados_ue0 = {
                        'tipo': 'ue_zero',
                        'tempo': tempo_simulacao,
                        'x': ue_zero.get_x(),
                        'y': ue_zero.get_y(),
                        'sinais': ue_zero.get_sinais(),
                        'distancias': ue_zero.get_distancias(),
                        'conectada_idx': getattr(ue_zero, 'estacao_conectada_idx', None),
                        'melhor_idx': getattr(ue_zero, 'melhor_estacao_idx', None),
                        'em_ligacao': getattr(ue_zero, 'em_ligacao', False),
                        'total_lu': ue_zero.get_total_updates(),
                        'total_pagings': getattr(ue_zero, 'total_pagings', 0),
                        'tac_atual': getattr(ue_zero, 'tac_atual', "--"),
                        'estacoes_em_paging_idx': paging_idx,
                        'momento_paging': getattr(ue_zero, 'momento_paging', None),
                        'vizinhas_idx': vizinhas_idx,
                        
                        'ttt_inicio': getattr(ue_zero, 'ttt_inicio', None),
                        'evento_handover': getattr(ue_zero, 'evento_handover_atual', "Nenhum"),
                        'total_handovers': getattr(ue_zero, 'total_handovers', 0)
                    }
                    fila_dados.put(dados_ue0)
                
                fila_dados.put({
                    'tipo': 'estatisticas',
                    'chunk_id': chunk_id,
                    'contagem_estacoes': contagem_local,
                    'total_lu': soma_lu_local,
                    'total_paging': soma_paging_local,
                    'total_handover': soma_handover_local,
                    'lu_estacoes': lu_por_estacao_local,
                    'paging_estacoes': paging_por_estacao_local
                })
                
    return {
        'chunk_id': chunk_id,
        'total_lu': soma_lu_local,
        'total_paging': soma_paging_local,
        'total_handover': soma_handover_local,
        'lu_estacoes': lu_por_estacao_local,
        'paging_estacoes': paging_por_estacao_local,
        'contagem_estacoes': contagem_local, 
        'tempo_final': tempo_simulacao
    }



# INICIALIZAÇÃO E CONTROLE
if __name__ == "__main__":
    
    manager = mp.Manager()

    if config.INTERFACE_GRAFICA:
        
        # MODO INTERFACE GRÁFICA
        print("\n[INFO] Iniciando simulação COM Interface Gráfica...")
        
        num_estacoes = len(config.ESTACOES_CONFIG)
        
        if config.POSICAO_ALEATORIA:
            print("[INFO] Posição aleatória habilitada. Gerando novas coordenadas para as estações...")
            posicoes = gerar_posicoes_estacoes(
                num_estacoes, 
                config.AREA_LARGURA, 
                config.AREA_ALTURA, 
                margem=30, 
                dist_minima=120 
            )
        else:
            print("[INFO] Usando lista de coordenadas fixas definida em POSICOES_FIXAS...")
            posicoes = config.POSICOES_FIXAS

        movimento_aleatorio = random_way_point.random_waypoint()
        movimento_mouse = mouse_movement.mouse_movement()
        model = okumura_hata.okumura_hata()

        estation_list = []
        for i, est_config_dict in enumerate(config.ESTACOES_CONFIG):
            config_temp = est_config_dict.copy()
            config_temp['CORD'] = posicoes[i]
            estation_list.append(estation.estation(config_temp))
       
        for est in estation_list:
            est.calcular_estacoes_vizinhas(estation_list)

        list_ue = []
        for i in range(config.quantidade_ue):
            if i == 0:
                list_ue.append(ue.ue(i, movimento_mouse, model, estation_list))
            else:
                list_ue.append(ue.ue(i, movimento_aleatorio, model, estation_list))

        stop_event = manager.Event()
        fila_dados = manager.Queue()
        fila_comandos = manager.Queue()
        
        num_cores = 1
        chunk_size = math.ceil(len(list_ue) / num_cores)
        chunks = [list_ue[i:i + chunk_size] for i in range(0, len(list_ue), chunk_size)]

        root = tk.Tk()
        root.title("Simulador de Handover com Multiprocessing")
        
        app = GUI.GUI(root, estation_list, fila_dados, fila_comandos)
        
        fila_interna = manager.Queue()

        def gerenciar_processos_background():
            memoria_chunks = {}
            with ProcessPoolExecutor(max_workers=len(chunks)) as executor:
                futuros = []
                for i, chunk in enumerate(chunks):
                    futuros.append(executor.submit(run_ue_chunk, chunk, stop_event, config.DELTA_T, fila_interna, fila_comandos, i, True, math.inf))
                
                while not stop_event.is_set():
                    try:
                        dados = fila_interna.get(timeout=0.5)
                        
                        if dados['tipo'] == 'ue_zero':
                            fila_dados.put(dados)
                            
                        elif dados['tipo'] == 'estatisticas':
                            memoria_chunks[dados['chunk_id']] = dados
                            
                            g_lu = sum(c['total_lu'] for c in memoria_chunks.values())
                            g_paging = sum(c['total_paging'] for c in memoria_chunks.values())
                            g_handover = sum(c['total_handover'] for c in memoria_chunks.values())
                            
                            g_estacoes = [0] * len(estation_list)
                            g_lu_estacoes = [0] * len(estation_list)
                            g_paging_estacoes = [0] * len(estation_list)
                            
                            for c in memoria_chunks.values():
                                for idx, qtd in enumerate(c['contagem_estacoes']):
                                    g_estacoes[idx] += qtd
                                for idx in range(len(estation_list)):
                                    g_lu_estacoes[idx] += c['lu_estacoes'][idx]
                                    g_paging_estacoes[idx] += c['paging_estacoes'][idx]
                                    
                            fila_dados.put({
                                'tipo': 'estatisticas',
                                'global_lu': g_lu,
                                'global_paging': g_paging,
                                'global_handover': g_handover,
                                'contagem_estacoes': g_estacoes,
                                'lu_estacoes': g_lu_estacoes,
                                'paging_estacoes': g_paging_estacoes
                            })
                    except queue.Empty:
                        pass
                print("\n[INFO] Simulação Visual Encerrada.")

        thread_motor = threading.Thread(target=gerenciar_processos_background, daemon=True)
        thread_motor.start()

        def fechar_janela():
            stop_event.set()
            root.destroy()
            sys.exit(0)

        root.protocol("WM_DELETE_WINDOW", fechar_janela)
        root.mainloop()

    else:
       
        # MODO TERMINAL (SEM INTERFACE)
        # ==========================================
        TEMPO_LIMITE_VIRTUAL = 3600
        num_estacoes = len(config.ESTACOES_CONFIG)
        
        # Verifica no config se o modo estatístico foi ativado
        modo_terminal = getattr(config, 'MODO_SIMULACAO', 'forca_bruta')
        
        if modo_terminal == 'estatistica':
            
            # MODO 1: ESTATÍSTICO
            NUM_SIMULACOES = getattr(config, 'NUM_SIMULACOES_ESTATISTICA', 10)
            
            print("\n" + "="*55)
            print(" [INFO] SIMULAÇÃO ESTATÍSTICA (MODO TERMINAL)")
            print("="*55)
            print(f"Repetições Programadas     : {NUM_SIMULACOES}")
            print(f"Tempo Virtual por cenário  : {TEMPO_LIMITE_VIRTUAL}s")
            print(f"Posição das Estações       : {'Aleatória' if config.POSICAO_ALEATORIA else 'Fixa (POSICOES_FIXAS)'}")
            print("="*55 + "\n")
            
            # Estruturas para guardar o histórico
            hist_lu_global = []
            hist_paging_global = []
            hist_ho_global = []
            
            hist_est_lu = [[] for _ in range(num_estacoes)]
            hist_est_paging = [[] for _ in range(num_estacoes)]
            hist_est_ue = [[] for _ in range(num_estacoes)]
            
            tempo_inicio_real = time.time()
            
            for sim_atual in range(1, NUM_SIMULACOES + 1):
                print(f"[Execução {sim_atual}/{NUM_SIMULACOES}] Rodando simulação estatística...")
                
                if config.POSICAO_ALEATORIA:
                    posicoes = gerar_posicoes_estacoes(num_estacoes, config.AREA_LARGURA, config.AREA_ALTURA)
                else:
                    posicoes = config.POSICOES_FIXAS
                
                movimento_aleatorio = random_way_point.random_waypoint()
                model = okumura_hata.okumura_hata()
                
                estation_list = []
                for i, est_config_dict in enumerate(config.ESTACOES_CONFIG):
                    config_temp = est_config_dict.copy()
                    config_temp['CORD'] = posicoes[i]
                    estation_list.append(estation.estation(config_temp))
                
                for est in estation_list:
                    est.calcular_estacoes_vizinhas(estation_list)
                    
                list_ue = []
                for i in range(config.quantidade_ue):
                    list_ue.append(ue.ue(i, movimento_aleatorio, model, estation_list))

                stop_event = manager.Event()
                num_cores = 10
                chunk_size = math.ceil(len(list_ue) / num_cores)
                chunks = [list_ue[i:i + chunk_size] for i in range(0, len(list_ue), chunk_size)]
               
                with ProcessPoolExecutor(max_workers=len(chunks)) as executor:
                    futuros = [
                        executor.submit(run_ue_chunk, chunk, stop_event, config.DELTA_T, None, None, i, False, TEMPO_LIMITE_VIRTUAL) 
                        for i, chunk in enumerate(chunks)
                    ]
                    resultados = [f.result() for f in futuros]
                
                # Consolidação dos resultados desta rodada
                rodada_lu = sum(r['total_lu'] for r in resultados)
                rodada_paging = sum(r['total_paging'] for r in resultados)
                rodada_ho = sum(r['total_handover'] for r in resultados)
                
                hist_lu_global.append(rodada_lu)
                hist_paging_global.append(rodada_paging)
                hist_ho_global.append(rodada_ho)
                
                for i_est in range(num_estacoes):
                    hist_est_lu[i_est].append(sum(r['lu_estacoes'][i_est] for r in resultados))
                    hist_est_paging[i_est].append(sum(r['paging_estacoes'][i_est] for r in resultados))
                    hist_est_ue[i_est].append(sum(r['contagem_estacoes'][i_est] for r in resultados))
            
            # -------------------------------------------------------------
            # GERAÇÃO DO ARQUIVO TXT
            # -------------------------------------------------------------
            nome_arquivo = "relatorio_estatistico.txt"
            
            with open(nome_arquivo, "a", encoding="utf-8") as f:
                f.write(f"=== RELATÓRIO ESTATÍSTICO DE {NUM_SIMULACOES} EXECUÇÕES ===\n")
                f.write(f"Tempo Virtual: {TEMPO_LIMITE_VIRTUAL}s | UEs: {config.quantidade_ue}\n")
                if not config.POSICAO_ALEATORIA:
                    f.write(f"Posições: {config.POSICOES_FIXAS}\n")
                f.write("-" * 50 + "\n")
                
                f.write("DADOS INDIVIDUAIS POR SIMULAÇÃO:\n")
                for i in range(NUM_SIMULACOES):
                    f.write(f"  Simu {i+1}: total de location update: {hist_lu_global[i]}, pagings: {hist_paging_global[i]}, handovers: {hist_ho_global[i]}\n")
                f.write("-" * 50 + "\n")
                
                # DADOS GLOBAIS
                f.write("DADOS GLOBAIS CONSOLIDADOS (Soma de todas as estações):\n")
                f.write(f"  LOCATION UPDATES -> Média: {statistics.mean(hist_lu_global):.2f} | Mediana: {statistics.median(hist_lu_global)} | Moda: {moda_segura(hist_lu_global)}\n")
                f.write(f"  PAGINGS          -> Média: {statistics.mean(hist_paging_global):.2f} | Mediana: {statistics.median(hist_paging_global)} | Moda: {moda_segura(hist_paging_global)}\n")
                f.write(f"  HANDOVERS        -> Média: {statistics.mean(hist_ho_global):.2f} | Mediana: {statistics.median(hist_ho_global)} | Moda: {moda_segura(hist_ho_global)}\n")
                f.write("-" * 50 + "\n")
                
                # DADOS POR ESTAÇÃO
                for i_est in range(num_estacoes):
                    f.write(f"ESTAÇÃO {i_est + 1} (TAC configurado: {config.ESTACOES_CONFIG[i_est]['TAC']}):\n")
                    f.write(f"  Location Updates -> Média: {statistics.mean(hist_est_lu[i_est]):.2f} | Mediana: {statistics.median(hist_est_lu[i_est])} | Moda: {moda_segura(hist_est_lu[i_est])}\n")
                    f.write(f"  Pagings          -> Média: {statistics.mean(hist_est_paging[i_est]):.2f} | Mediana: {statistics.median(hist_est_paging[i_est])} | Moda: {moda_segura(hist_est_paging[i_est])}\n")
                    f.write(f"  Qtd. UEs (Final) -> Média: {statistics.mean(hist_est_ue[i_est]):.2f} | Mediana: {statistics.median(hist_est_ue[i_est])} | Moda: {moda_segura(hist_est_ue[i_est])}\n")
                    f.write("\n")
            
            print(f"\n[OK] Simulação Concluída. Resultados salvos em: '{nome_arquivo}'")
            
            # -------------------------------------------------------------
            # GERAÇÃO DOS GRÁFICOS (MATPLOTLIB)
            # -------------------------------------------------------------
            print("\n[INFO] Gerando gráficos estatísticos...")
            try:
                import matplotlib.pyplot as plt
                
                os.makedirs("graficos", exist_ok=True)
                
                # Formatando as posições para caberem na caixa de texto
                posicoes_str = ", ".join([f"E{i+1}: {pos}" for i, pos in enumerate(posicoes)])
                
                # Texto com as informações do cenário
                info_cenario = (
                    f"CENÁRIO DA SIMULAÇÃO\n"
                    f"UEs: {config.quantidade_ue} | Tempo Simulado: {TEMPO_LIMITE_VIRTUAL}s\n"
                    f"Posições: {posicoes_str}"
                )
                
                # --- Gráfico 1: Linhas de Evolução Global ---
                fig1 = plt.figure(figsize=(12, 8))
                simulacoes_x = range(1, NUM_SIMULACOES + 1)
                
                plt.plot(simulacoes_x, hist_lu_global, marker='o', linestyle='-', color='blue', label='Location Updates')
                plt.plot(simulacoes_x, hist_paging_global, marker='s', linestyle='-', color='red', label='Pagings')
                plt.plot(simulacoes_x, hist_ho_global, marker='^', linestyle='-', color='green', label='Handovers')
                
                plt.title('Evolução de Eventos ao Longo das Simulações', fontsize=14, pad=15)
                plt.xlabel('Número da Simulação', fontsize=12)
                plt.ylabel('Quantidade Total de Eventos', fontsize=12)
                plt.legend()
                plt.grid(True, linestyle='--', alpha=0.7)
                
                # CORREÇÃO DO EIXO X: Mostra todos se forem poucos, ou pula de 10 em 10 se forem muitos
                if NUM_SIMULACOES <= 20:
                    plt.xticks(simulacoes_x)
                else:
                    passo = max(1, NUM_SIMULACOES // 10)
                    plt.xticks(range(0, NUM_SIMULACOES + 1, passo))
                
                # Adicionando a caixa de cenário no rodapé
                plt.figtext(0.5, 0.02, info_cenario, wrap=True, horizontalalignment='center', 
                            fontsize=10, bbox={'facecolor': '#f0f0f0', 'alpha': 0.8, 'pad': 8, 'edgecolor': '#cccccc'})
                
                # Empurra o gráfico um pouco para cima para caber o texto
                plt.subplots_adjust(bottom=0.2)
                
                plt.savefig("graficos/1_eventos_globais_evolucao.png", dpi=300)
                plt.close(fig1)
                
                # --- Gráfico 2: Médias por Estação (Gráfico de Barras com TAC) ---
                fig2, ax = plt.subplots(figsize=(12, 8))
                
                # Labels com TAC incluso
                estacoes_labels = [f"Estação {i+1}\n(TAC: {config.ESTACOES_CONFIG[i]['TAC']})" for i in range(num_estacoes)]
                medias_lu = [statistics.mean(hist_est_lu[i]) for i in range(num_estacoes)]
                medias_pag = [statistics.mean(hist_est_paging[i]) for i in range(num_estacoes)]
                
                x = range(num_estacoes)
                width = 0.35  
                
                ax.bar([pos - width/2 for pos in x], medias_lu, width, label='Média LU', color='royalblue')
                ax.bar([pos + width/2 for pos in x], medias_pag, width, label='Média Paging', color='crimson')
                
                ax.set_ylabel('Quantidade Média', fontsize=12)
                ax.set_title('Média de Eventos por Estação', fontsize=14, pad=15)
                ax.set_xticks(x)
                ax.set_xticklabels(estacoes_labels, fontsize=11)
                ax.legend()
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                
                # Adicionando a caixa de cenário no rodapé
                plt.figtext(0.5, 0.02, info_cenario, wrap=True, horizontalalignment='center', 
                            fontsize=10, bbox={'facecolor': '#f0f0f0', 'alpha': 0.8, 'pad': 8, 'edgecolor': '#cccccc'})
                
                # Empurra o gráfico um pouco para cima para caber o texto
                plt.subplots_adjust(bottom=0.2)
                
                plt.savefig("graficos/2_medias_por_estacao.png", dpi=300)
                plt.close(fig2)

                print(f"[OK] 2 gráficos foram gerados com sucesso na pasta 'graficos/'.")
            
            except ImportError:
                print(f"\n[AVISO] A biblioteca 'matplotlib' não está instalada.")
                print(f"Os arquivos de texto foram salvos, mas os gráficos não puderam ser gerados.")
                print(f"Para corrigir isso, instale abrindo o terminal e digitando: pip install matplotlib")

            print(f"Tempo total de processamento: {time.time() - tempo_inicio_real:.2f} segundos.")
            
        else:
            
            # MODO 2: FORÇA BRUTA PARA TAC
            NUM_LOCATION_AREAS = 3
            NUM_SIMULACOES = 1
            
            valores_tac = list(range(NUM_LOCATION_AREAS))
            combinacoes = list(itertools.product(valores_tac, repeat=num_estacoes))
            
            print("\n" + "="*55)
            print(" [INFO] SIMULAÇÃO FORÇA BRUTA (OTIMIZAÇÃO TAC)")
            print("="*55)
            print(f"Número de simulações em fila: {NUM_SIMULACOES}")
            print(f"Estações mapeadas          : {num_estacoes}")
            print(f"TACs permitidos            : {NUM_LOCATION_AREAS} (Faixa: 0 a {NUM_LOCATION_AREAS-1})")
            print(f"Total de cenários por ciclo: {len(combinacoes)}")
            print(f"Tempo Virtual por cenário  : {TEMPO_LIMITE_VIRTUAL}s")
            print(f"Posição das Estações       : {'Aleatória' if config.POSICAO_ALEATORIA else 'Fixa (POSICOES_FIXAS)'}")
            print("="*55 + "\n")
            
            tempo_inicio_real_total = time.time()
            
            for sim_atual in range(1, NUM_SIMULACOES + 1):
                print(f"\n" + ">"*20 + f" INICIANDO SIMULAÇÃO {sim_atual} DE {NUM_SIMULACOES} " + "<"*20)
                
                if config.POSICAO_ALEATORIA:
                    posicoes = gerar_posicoes_estacoes(
                        num_estacoes, config.AREA_LARGURA, config.AREA_ALTURA, margem=30, dist_minima=120
                    )
                else:
                    posicoes = config.POSICOES_FIXAS
                
                resultados_gerais = []
                
                for idx_cenario, combinacao in enumerate(combinacoes):
                    print(f"[Simulação {sim_atual}/{NUM_SIMULACOES}] -> Executando Cenário {idx_cenario} | Matriz TAC: {list(combinacao)}...")
                    
                    movimento_aleatorio = random_way_point.random_waypoint()
                    model = okumura_hata.okumura_hata()

                    estation_list = []
                    for i, est_config_dict in enumerate(config.ESTACOES_CONFIG):
                        config_temp = est_config_dict.copy()
                        config_temp['TAC'] = combinacao[i]
                        config_temp['TAC_LIST'] = [combinacao[i]] 
                        config_temp['CORD'] = posicoes[i]
                        estation_list.append(estation.estation(config_temp))
                   
                    for est in estation_list:
                        est.calcular_estacoes_vizinhas(estation_list)

                    list_ue = []
                    for i in range(config.quantidade_ue):
                        list_ue.append(ue.ue(i, movimento_aleatorio, model, estation_list))

                    stop_event = manager.Event()
                    num_cores = 10
                    chunk_size = math.ceil(len(list_ue) / num_cores)
                    chunks = [list_ue[i:i + chunk_size] for i in range(0, len(list_ue), chunk_size)]
                   
                    with ProcessPoolExecutor(max_workers=len(chunks)) as executor:
                        futuros = []
                        for i_chunk, chunk in enumerate(chunks):
                            futuros.append(executor.submit(
                                run_ue_chunk, chunk, stop_event, config.DELTA_T, None, None, i_chunk, False, TEMPO_LIMITE_VIRTUAL
                            ))
                        
                        resultados = [f.result() for f in futuros]

                    # Calcula o custo total desta combinação
                    custo_total_cenario = 0
                    for r in resultados:
                        for i_est in range(num_estacoes):
                            lu = r['lu_estacoes'][i_est]
                            pagings = r['paging_estacoes'][i_est]
                            custo_total_cenario += lu + (10 * pagings)
                    
                    resultados_gerais.append({
                        'combinacao': list(combinacao),
                        'custo_total': custo_total_cenario
                    })
                    
                # Geração do relatório
                resultados_ordenados = sorted(resultados_gerais, key=lambda x: x['custo_total'])
                top_4 = resultados_ordenados[:4]
                
                nome_arquivo = "melhor_configuracao_tac.txt"
                
                with open(nome_arquivo, "a", encoding="utf-8") as f:
                    melhor_comb = top_4[0]['combinacao']
                    f.write(f"Posições: {posicoes} = {melhor_comb} | UEs: {config.quantidade_ue} | Tempo: {TEMPO_LIMITE_VIRTUAL}s\n")
                    
                    for i in range(1, len(top_4)):
                        res = top_4[i]
                        f.write(f"  {i+1}º Lugar: {res['combinacao']}\n")
                        
                    f.write("-" * 60 + "\n") 

                print("="*55)
                print(f"\nTOP 4 Melhores Configurações da Simulação {sim_atual}:")
                for i, res in enumerate(top_4):
                    print(f"  {i+1}º Lugar: {res['combinacao']} | Custo: {res['custo_total']}")
                print(f"\n[OK] Dados da Simulação {sim_atual} anexados no arquivo: '{nome_arquivo}'")
                print("="*55)

            tempo_fim_real_total = time.time()
            print(f"\n[FIM DO PROCESSO LOTE] Todas as {NUM_SIMULACOES} simulações foram concluídas!")
            print(f"Tempo total gasto: {tempo_fim_real_total - tempo_inicio_real_total:.2f} segundos.")