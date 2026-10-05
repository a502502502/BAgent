import penaltyblog as pb
import pandas as pd

# Create a small dataset of matches
matches = pd.DataFrame([
    {"home_team": "Velez", "away_team": "Platense", "home_goals": 1, "away_goals": 0},
    {"home_team": "Platense", "away_team": "Banfield", "home_goals": 1, "away_goals": 1},
    {"home_team": "Banfield", "away_team": "Velez", "home_goals": 0, "away_goals": 2},
    {"home_team": "Rosario", "away_team": "Velez", "home_goals": 1, "away_goals": 1},
    {"home_team": "Platense", "away_team": "Rosario", "home_goals": 0, "away_goals": 0},
    {"home_team": "Rosario", "away_team": "Banfield", "home_goals": 2, "away_goals": 1},
])

model = pb.models.DixonColesGoalModel(
    matches["home_goals"],
    matches["away_goals"],
    matches["home_team"],
    matches["away_team"]
)
model.fit()

# Predict next match: Velez vs Platense
preds = model.predict("Velez", "Platense")
print("Velez vs Platense Dixon-Coles prediction:")
print("  Home win:", round(preds.home_win, 4))
print("  Draw:", round(preds.draw, 4))
print("  Away win:", round(preds.away_win, 4))
print("  Over 2.5:", round(preds.total_goals("over", 2.5), 4))
print("  Under 2.5:", round(preds.total_goals("under", 2.5), 4))
print("  Both teams to score:", round(preds.btts, 4))
