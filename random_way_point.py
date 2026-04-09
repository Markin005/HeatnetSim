import random
import math
from movement_model import movement_model


class random_waypoint(movement_model):
    def __init__(self):
        pass

    def _novo_destino(self, width, height):
        """Gera um novo ponto destino aleatório."""
        x = random.randint(0, width)
        y = random.randint(0, height)
        return (x, y)

    def mover(self, ue, width, height):
        """Move a UE em direção a um destino aleatório."""
        
        vel = ue.get_velocidade()
        x = ue.get_x()
        y = ue.get_y()

        # Se ainda não existe destino, escolhe um
        if ue.get_destiny() is None:
            ue.set_destiny(self._novo_destino(width, height))

        dest_x, dest_y = ue.get_destiny()

        # Calcula distância até o destino
        dx = dest_x - x
        dy = dest_y - y
        distancia = math.hypot(dx, dy)

        # Se chegou no destino (ou está muito perto)
        if distancia < vel:
            # Chegou -> define novo destino
            ue.set_x(dest_x)
            ue.set_y(dest_y)
            ue.set_destiny(self._novo_destino(width, height))
            return

        # Movimento normal (vetor unitário)
        x += vel * (dx / distancia)
        y += vel * (dy / distancia)

        # Atualiza posição
        ue.set_x(x)
        ue.set_y(y)

