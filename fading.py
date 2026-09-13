import math
import random


class GaussianFadingModel:
    """Fading gaussiano por link."""

    def __init__(
        self,
        *,
        habilitado=False,
        sigma_db=0.0,
        tempo_correlacao_s=0.0,
        tempo_estabilidade_s=0.0,
        delta_t_s=0.0,
        seed=None,
    ):
        self.habilitado = bool(habilitado) and float(sigma_db) > 0.0
        self.sigma_db = float(sigma_db)
        self.tempo_correlacao_s = float(tempo_correlacao_s)
        self.tempo_estabilidade_s = float(tempo_estabilidade_s)
        self.delta_t_s = float(delta_t_s)
        self._rng = random.Random(seed)
        self._estado_por_link = {}
        self._hold_por_link = {}

    def _delta_t_fading(self):
        if self.tempo_estabilidade_s > 0.0:
            return self.tempo_estabilidade_s
        return self.delta_t_s

    def _passos_hold(self):
        if self.tempo_estabilidade_s <= 0.0 or self.delta_t_s <= 0.0:
            return 1
        return max(1, math.ceil(self.tempo_estabilidade_s / self.delta_t_s))

    def _rho(self):
        delta_t_fading = self._delta_t_fading()
        if self.tempo_correlacao_s <= 0.0 or delta_t_fading <= 0.0:
            return 0.0
        return math.exp(-delta_t_fading / self.tempo_correlacao_s)

    def _amostrar_novo_db(self, link_id=None):
        rho = self._rho()
        if rho <= 0.0 or link_id is None:
            return self._rng.gauss(0.0, self.sigma_db)

        anterior = self._estado_por_link.get(link_id)
        if anterior is None:
            anterior = self._rng.gauss(0.0, self.sigma_db)

        inovacao_sigma = self.sigma_db * math.sqrt(max(0.0, 1.0 - (rho * rho)))
        atual = (rho * anterior) + self._rng.gauss(0.0, inovacao_sigma)
        self._estado_por_link[link_id] = atual
        return atual

    def amostrar_db(self, link_id=None):
        if not self.habilitado:
            return 0.0

        if self.tempo_estabilidade_s <= 0.0 or link_id is None:
            return self._amostrar_novo_db(link_id=link_id)

        valor_hold, restantes = self._hold_por_link.get(link_id, (None, 0))
        if valor_hold is not None and restantes > 0:
            self._hold_por_link[link_id] = (valor_hold, restantes - 1)
            return valor_hold

        atual = self._amostrar_novo_db(link_id=link_id)
        self._hold_por_link[link_id] = (atual, self._passos_hold() - 1)
        return atual

    def aplicar(self, rsrp_base, link_id=None):
        return float(rsrp_base) + self.amostrar_db(link_id=link_id)
