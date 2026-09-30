"""Il modello gol del sesto senso usa i lambda corretti, non solo l'1X2."""

from services.football.base_model.goal_model import GoalModel
from services.football.sixth_sense.analyzer import SixthSenseEvent
from services.football.sixth_sense.lambda_context import context_from_events, project_attack


def test_goal_model_shrinks_when_the_home_striker_is_out():
    base = GoalModel.from_win_prob(home_win=0.55)
    events = [SixthSenseEvent("home", "injury", "punta titolare fuori", impact=-2.0, confidence=1.0)]
    attack = project_attack(base.lh, base.la, context_from_events(events))
    model = GoalModel(lambda_home=attack.xg_home, lambda_away=attack.xg_away)
    assert model.lh < base.lh
    assert model.la == base.la
    assert attack.base_home == base.lh
    assert any("assenza offensiva casa" in note for note in attack.notes)
