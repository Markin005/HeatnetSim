import tkinter as tk
import GUI
import ue
import estation
import okumura_hata
import random_way_point
import config

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Simulation Loop")

    # Modelos
    movement = random_way_point.random_waypoint()
    model = okumura_hata.okumura_hata()

    # Estações 
    estation_list = []
    for est_config_dict in config.ESTACOES_CONFIG:
        estation_list.append(estation.estation(est_config_dict))
   
    # Cada estação procurar suas vizinhas
    for est in estation_list:
        est.calcular_estacoes_vizinhas(estation_list)

    # UEs
    list_ue = []
    for i in range(config.quantidade_ue):
        list_ue.append(ue.ue(i, movement, model, estation_list))

    # GUI
    app = GUI.GUI(root, list_ue, estation_list)

    # Conexao GUI e UE
    for uma_ue in list_ue:
        uma_ue.registrar_callback_visual(app.receber_ordem_de_desenho)

    # 5. Start
    root.mainloop()