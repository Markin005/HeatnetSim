import math

class movement_model:
    def __init__(self):
        pass

    def medir_distancia(self,x_ue,y_ue,x_estation,y_estation):
        distancia = math.sqrt((x_ue - x_estation)**2 + (y_ue - y_estation)**2)
        return distancia
