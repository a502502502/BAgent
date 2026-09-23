import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8')
from services.analysis.xg_poisson_engine import QuantitativeEngine

def main():
    engine = QuantitativeEngine()

    fixtures = [
        {
            "match": "OH Leuven W vs Roma W",
            "comp": "UEFA Women Champions League",
            "time": "18:45 CEST",
            "xg_h": 0.8, "xg_a": 2.2,
            "candidates": [("Over 1.5", 1.22), ("2", 1.45), ("X2 + Over 1.5", 1.35), ("MultiGol 2-5", 1.30)]
        },
        {
            "match": "Servette W vs Lione W",
            "comp": "UEFA Women Champions League",
            "time": "18:45 CEST",
            "xg_h": 0.4, "xg_a": 3.1,
            "candidates": [("Over 2.5", 1.25), ("2 + Over 2.5", 1.33), ("MultiGol 2-5", 1.30)]
        },
        {
            "match": "Barcellona W vs Paris FC W",
            "comp": "UEFA Women Champions League",
            "time": "21:00 CEST",
            "xg_h": 3.4, "xg_a": 0.5,
            "candidates": [("Over 2.5", 1.22), ("1 + Over 2.5", 1.28), ("Over 1.5", 1.08)]
        },
        {
            "match": "Chelsea W vs Austria Vienna W",
            "comp": "UEFA Women Champions League",
            "time": "21:00 CEST",
            "xg_h": 2.8, "xg_a": 0.5,
            "candidates": [("Over 2.5", 1.25), ("1 + Over 1.5", 1.20), ("1X + Over 1.5", 1.18), ("MultiGol 2-5", 1.32)]
        },
        {
            "match": "Santa Fe vs Deportivo Cali",
            "comp": "Colombia Primera A",
            "time": "23:00 CEST",
            "xg_h": 1.5, "xg_a": 0.8,
            "candidates": [("1X", 1.25), ("Under 2.5", 1.55), ("MultiGol 1-3", 1.35)]
        }
    ]

    print("=== CALCOLO PROBABILITA POISSON PER STASERA ===")
    for f in fixtures:
        print(f"\n⚽ {f['match']} ({f['comp']} - {f['time']})")
        for m, odd in f['candidates']:
            p = engine.goal_market_probability(f['xg_h'], f['xg_a'], m)
            fair = 1 / p if p > 0 else 0
            edge = (p * odd) - 1.0
            print(f"   {m:<18} | Quota: {odd:.2f} | P(Poisson): {p*100:5.1f}% | Fair: {fair:.2f} | Edge: {edge*100:+5.1f}%")

if __name__ == "__main__":
    main()
