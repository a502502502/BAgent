import pandas as pd
import numpy as np
import math
from pathlib import Path

DECAY=2.0
ROOT=Path("data/football/raw/serie_b")

# Coefficienti V3 OOS 2021-2025
B=np.array([
 [ 0.1867922818575245, -0.024947632672247793, -0.161844649185277 ],
 [-0.19821256204331952,  0.33053783967204625, -0.1323252776287272 ],
 [ 0.22087364555620967, -0.09534769021911586, -0.12552595543617814 ],
 [ 1.0149503893855993, -0.24551090406549386, -0.7694394853201072 ],
 [-0.15382086055043118,  0.14650094597487995,  0.007319914575552085 ],
 [-0.6743372469776423,  0.07406232541836634,  0.6002749215592763 ],
])

def devig(h,d,a):
    x=np.array([1/h,1/d,1/a],float)
    return x/x.sum()

def stats(rows,team,date):
    w=gf=ga=wt=0.0
    for r in rows:
        if r["home"]!=team and r["away"]!=team:
            continue
        days=max(0,(date-r["date"]).days)
        z=math.exp(-DECAY*days/365.0)
        if r["home"]==team:
            f,a=r["hg"],r["ag"]
        else:
            f,a=r["ag"],r["hg"]
        w += z*(f>a)
        gf += z*f
        ga += z*a
        wt += z
    return None if wt==0 else (w/wt,(gf-ga)/wt)

rows=[]

for f in sorted(ROOT.glob("BRB_*.csv")):
    df=pd.read_csv(f)
    for _,r in df.iterrows():
        if str(r["status"]).lower()!="complete":
            continue
        date=pd.to_datetime(int(r["timestamp"]),unit="s")
        if date >= pd.Timestamp("2026-08-11"):
            continue
        rows.append({
            "date":date,
            "home":str(r["home_team_name"]),
            "away":str(r["away_team_name"]),
            "hg":int(r["home_team_goal_count"]),
            "ag":int(r["away_team_goal_count"])
        })

rows.sort(key=lambda x:x["date"])

home="Avaí"
away="CRB"

hs=stats(rows,home,pd.Timestamp("2026-08-11"))
as_=stats(rows,away,pd.Timestamp("2026-08-11"))

# Snapshot mercato precedente: 2.61 / 3.20 / 2.70
market=devig(2.61,3.20,2.70)

X=np.array([[
    1.0,
    hs[0]-as_[0],
    hs[1]-as_[1],
    *market
]])

z=X@B
z-=z.max(axis=1,keepdims=True)
p=np.exp(z)
p/=p.sum(axis=1,keepdims=True)

print()
print("="*60)
print("AVAÍ - CRB | V3 PROVVISORIA")
print("="*60)
print("HISTORICAL MATCHES:",len(rows))
print("RECENCY:",DECAY)
print("MARKET SNAPSHOT: 2.61 / 3.20 / 2.70")
print()
print("HOME :",f"{p[0,0]:.4f} FAIR={1/p[0,0]:.2f}")
print("DRAW :",f"{p[0,1]:.4f} FAIR={1/p[0,1]:.2f}")
print("AWAY :",f"{p[0,2]:.4f} FAIR={1/p[0,2]:.2f}")
print()
print("HOME RECENCY:",hs)
print("AWAY RECENCY:",as_)
print("MARKET DEVIG:",market)
print()
print("MODEL:",["HOME","DRAW","AWAY"][int(np.argmax(p[0]))])
print("STATUS: PROVISIONAL - NOT VALIDATED FOR LIVE BETTING")
