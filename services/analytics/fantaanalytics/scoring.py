"""Versioned, role-aware, explainable deterministic Fanta Score baseline."""

from dataclasses import dataclass
from typing import Iterable, List, Tuple

from .models import NormalizedPlayer

MODEL_VERSION = "deterministic-v1"


@dataclass(frozen=True)
class ScoreComponent:
    label: str
    value: float


@dataclass(frozen=True)
class PlayerScore:
    external_id: str
    fantasy_role: str
    score: float
    tier: str
    reliability: float
    risk: float
    components: Tuple[ScoreComponent, ...]
    explanation_it: str
    model_version: str = MODEL_VERSION


def _clip(value: float) -> float:
    return max(0.0, min(1.0, value))


def _tier(score: float) -> str:
    if score >= 82:
        return "S"
    if score >= 70:
        return "A"
    if score >= 58:
        return "B"
    if score >= 46:
        return "C"
    if score >= 34:
        return "D"
    return "Watchlist" if score >= 24 else "Avoid"


def score_player(player: NormalizedPlayer) -> PlayerScore:
    """Score one player without pretending missing statistics are zero production."""
    minutes_ratio = _clip((player.minutes or 900) / 2700)
    starter = player.starter_probability if player.starter_probability is not None else 0.5
    rotation = player.rotation_risk if player.rotation_risk is not None else 0.35
    injury = player.injury_risk if player.injury_risk is not None else 0.15
    team_strength = player.team_strength if player.team_strength is not None else 0.5
    fantasy_average = player.fantasy_average if player.fantasy_average is not None else 6.0
    form_ratio = _clip((fantasy_average - 5.0) / 3.5)
    minutes = player.minutes or 900
    per90 = ((player.goals or 0) + (player.assists or 0)) * 90 / max(minutes, 1)
    role_target = {"P": 0.10, "D": 0.22, "C": 0.42, "A": 0.65}[player.fantasy_role]
    bonus_ratio = _clip(per90 / role_target) if role_target else 0.0
    special_duties = (1.0 if player.penalty_taker else 0.0) + (
        0.6 if player.set_piece_taker else 0.0
    )
    risk_ratio = _clip((rotation * 0.6) + (injury * 0.4))
    components = (
        ScoreComponent("Minuti attesi", round(minutes_ratio * 25, 1)),
        ScoreComponent("Probabilità di titolarità", round(starter * 20, 1)),
        ScoreComponent("Rendimento storico", round(form_ratio * 25, 1)),
        ScoreComponent("Produzione bonus per 90", round(bonus_ratio * 15, 1)),
        ScoreComponent("Forza della squadra", round(team_strength * 7, 1)),
        ScoreComponent("Rigori e piazzati", round(special_duties * 3.1, 1)),
        ScoreComponent("Rischio infortuni e rotazioni", round(-risk_ratio * 12, 1)),
    )
    score = round(max(0.0, min(100.0, sum(item.value for item in components))), 1)
    reliability = round(_clip(minutes_ratio * 0.55 + starter * 0.45 - risk_ratio * 0.15) * 100, 1)
    risk = round(_clip(risk_ratio * 0.75 + (1 - minutes_ratio) * 0.25) * 100, 1)
    strengths = sorted(
        (component for component in components if component.value > 0),
        key=lambda item: item.value,
        reverse=True,
    )
    primary = strengths[0].label.lower() if strengths else "dati disponibili"
    caution = "" if risk < 40 else " Il rischio di rotazione o infortunio richiede prudenza."
    explanation = (
        f"Profilo {_tier(score)} per {player.fantasy_role}: il contributo principale deriva da "
        f"{primary}. Affidabilità {reliability:.0f}/100 e rischio {risk:.0f}/100.{caution}"
    )
    return PlayerScore(
        external_id=player.external_id,
        fantasy_role=player.fantasy_role,
        score=score,
        tier=_tier(score),
        reliability=reliability,
        risk=risk,
        components=components,
        explanation_it=explanation,
    )


def score_players(players: Iterable[NormalizedPlayer]) -> List[PlayerScore]:
    return [score_player(player) for player in players]
