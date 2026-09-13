import math
from movement_model import movement_model
import config

class mouse_movement(movement_model):
    def __init__(self):
        pass

    def mover(self, ue, width, height):
        
        # Se não existe destino (ainda não clicou ou já chegou), a UE fica parada.
        if ue.get_destiny() is None:
            return

        vel = ue.get_velocidade() * config.DELTA_T
        x = ue.get_x()
        y = ue.get_y()
        dest_x, dest_y = ue.get_destiny()

        # Calcula distância até o destino
        dx = dest_x - x
        dy = dest_y - y
        distancia = math.hypot(dx, dy)

        # Se chegou no destino (ou está muito perto)
        if distancia < vel:
            # Chegou -> Crava na posição e apaga o destino para ela parar
            ue.set_x(dest_x)
            ue.set_y(dest_y)
            ue.set_destiny(None)
            return

        # Movimento normal (vetor unitário)
        x += vel * (dx / distancia)
        y += vel * (dy / distancia)

        # Atualiza posição
        ue.set_x(x)
        ue.set_y(y)