
import random
from movement_model import movement_model

class random_walk(movement_model):
    def __init__(self):
        pass

    def mover(self, ue, width, height):
        """Move a UE de forma aleatória dentro da área delimitada"""

        direcao = random.choice(["cima", "baixo", "esquerda", "direita"])
        vel = ue.get_velocidade()

        x = ue.get_x()
        y = ue.get_y()

        # Movimento
        if direcao == "cima":
            y -= vel
        elif direcao == "baixo":
            y += vel
        elif direcao == "esquerda":
            x -= vel
        elif direcao == "direita":
            x += vel

        # Teletransporte nas bordas
        if x < 0:
            x = width
        elif x > width:
            x = 0

        if y < 0:
            y = height
        elif y > height:
            y = 0

        # Aplicando alterações via SETTERS
        ue.set_x(x)
        ue.set_y(y)
