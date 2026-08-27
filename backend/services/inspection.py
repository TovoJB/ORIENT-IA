"""Mode inspection : état global contrôlé depuis l'interface.

- `mode` : active la collecte du raisonnement (filtrage Prolog, règles, ML, fusion)
  renvoyé dans chaque recommandation pour affichage en temps réel.
- `force_prolog` : désactive temporairement `rules_fallback` et force
  l'utilisation EXCLUSIVE du moteur SWI-Prolog (pyswip). Si SWI-Prolog est
  absent, les appels Prolog lèvent `PrologUnavailable`.
"""


class PrologUnavailable(Exception):
    """Levée quand le mode 'prolog exclusif' est actif sans SWI-Prolog."""


class _InspectionState:
    def __init__(self) -> None:
        self.mode = False
        self.force_prolog = False


state = _InspectionState()
