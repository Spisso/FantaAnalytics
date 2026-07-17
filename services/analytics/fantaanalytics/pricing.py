"""League-budget coherent, explainable baseline auction pricing."""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .scoring import PlayerScore


@dataclass(frozen=True)
class LeagueConfig:
    participants: int = 10
    budget: int = 1000
    minimum_bid: int = 1
    role_slots: Dict[str, int] = field(default_factory=lambda: {"P": 3, "D": 8, "C": 8, "A": 6})
    role_budget_shares: Dict[str, float] = field(
        default_factory=lambda: {"P": 0.08, "D": 0.15, "C": 0.32, "A": 0.45}
    )

    def validate(self) -> None:
        if self.participants < 2 or self.budget <= 0 or self.minimum_bid < 1:
            raise ValueError("Configurazione lega non valida")
        if set(self.role_slots) != {"P", "D", "C", "A"} or set(self.role_budget_shares) != set(
            self.role_slots
        ):
            raise ValueError("Ruoli della lega incompleti")
        if any(slots < 1 for slots in self.role_slots.values()):
            raise ValueError("Ogni ruolo deve avere almeno uno slot")
        if round(sum(self.role_budget_shares.values()), 6) != 1:
            raise ValueError("Le quote budget per ruolo devono sommare a 1")


@dataclass(frozen=True)
class PricePrediction:
    external_id: str
    baseline_price: float
    minimum_recommended_price: float
    maximum_recommended_price: float
    confidence: float
    price_to_value: float
    status: str
    explanation_it: str


def predict_prices(scores: Iterable[PlayerScore], league: LeagueConfig) -> List[PricePrediction]:
    """Distribute the complete league budget across roles and available players."""
    league.validate()
    grouped: Dict[str, List[PlayerScore]] = {role: [] for role in league.role_slots}
    for score in scores:
        if score.fantasy_role in grouped:
            grouped[score.fantasy_role].append(score)
    output: List[PricePrediction] = []
    for role, players in grouped.items():
        if not players:
            continue
        full_role_pool = league.participants * league.budget * league.role_budget_shares[role]
        expected_supply = league.participants * league.role_slots[role]
        # A partial shortlist must not absorb money reserved for players not present.
        # With a complete pool this is exactly the configured role budget.
        coverage = min(1.0, len(players) / expected_supply)
        role_pool = full_role_pool * coverage
        weights = [max(0.5, score.score) for score in players]
        total_weight = sum(weights)
        allocated = 0.0
        for index, (score, weight) in enumerate(zip(players, weights)):
            # Keep the rounded distribution coherent with the exact league budget.
            baseline = (
                round(role_pool - allocated, 2)
                if index == len(players) - 1
                else round(role_pool * weight / total_weight, 2)
            )
            allocated += baseline
            confidence = round(
                max(20.0, min(90.0, score.reliability * 0.8 + (100 - score.risk) * 0.2)), 1
            )
            maximum = round(max(league.minimum_bid, baseline * (0.92 + confidence / 500)), 2)
            minimum = round(max(league.minimum_bid, baseline * 0.82), 2)
            status = "sottovalutato" if score.score / max(baseline, 1) > 0.9 else "equo"
            output.append(
                PricePrediction(
                    external_id=score.external_id,
                    baseline_price=baseline,
                    minimum_recommended_price=minimum,
                    maximum_recommended_price=maximum,
                    confidence=confidence,
                    price_to_value=round(baseline / max(score.score, 1), 2),
                    status=status,
                    explanation_it=(
                        f"Stima basata su score {score.score:.1f}, affidabilità {score.reliability:.0f}/100 "
                        f"e quota budget del ruolo {role} (copertura pool {coverage:.0%})."
                    ),
                )
            )
    return output
