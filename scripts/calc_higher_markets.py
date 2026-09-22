import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from services.analysis.xg_poisson_engine import QuantitativeEngine
import numpy as np

qe = QuantitativeEngine(rho=-0.05)

matches = [
    ('Barnsley vs Leeds U21', 2.30, 1.10, 6.2, 4.2),
    ('Rochdale vs Liverpool U21', 1.60, 1.80, 5.2, 5.8),
    ('Peterborough vs Colchester', 2.10, 0.90, 6.5, 3.8),
    ('Juventus W vs Benfica W', 2.10, 0.80, 6.0, 3.5),
    ('Arsenal W vs HB Koege', 3.20, 0.30, 8.0, 2.0),
    ('Salford City vs Sheffield Wed', 1.10, 1.60, 4.5, 5.5),
]

print(f"{'PARTITA':<30} | {'O1.5':<6} | {'O2.5':<6} | {'GOL/GG':<7} | {'MG 2-4':<7} | {'O8.5C':<6}")
print("-" * 75)

for name, xh, xa, ch, ca in matches:
    mat = qe.generate_score_matrix(xh, xa)
    gr = np.arange(7)
    grid = gr[:, None] + gr[None, :]
    
    po15 = float(np.sum(mat[grid > 1.5]))
    po25 = float(np.sum(mat[grid > 2.5]))
    
    # Entrambe segnano: i > 0 and j > 0
    pgg = float(np.sum(mat[1:, 1:]))
    
    # Multigol 2-4
    pmg24 = float(np.sum(mat[(grid >= 2) & (grid <= 4)]))
    
    # Corner
    rc = qe.analyze_corners('H', 'A', ch, ca)
    po85c = rc['corner_markets']['Over 8.5 Corner Totali']['prob']
    
    fair_o25 = 1.0 / po25 if po25 > 0 else 0
    fair_gg = 1.0 / pgg if pgg > 0 else 0
    fair_mg = 1.0 / pmg24 if pmg24 > 0 else 0
    
    print(f"{name:<30} | {po15*100:4.1f}% | {po25*100:4.1f}% (@{fair_o25:.2f}) | {pgg*100:5.1f}% (@{fair_gg:.2f}) | {pmg24*100:5.1f}% (@{fair_mg:.2f}) | {po85c*100:4.1f}%")
