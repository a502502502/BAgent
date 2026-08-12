from pathlib import Path
import pandas as pd
import numpy as np
import math

DECAY=2.0
ITERATIONS=8000
LR=0.03
L2=0.001
ROOT=Path("data/football/raw/serie_b")

def softmax(z):
    z=z-np.max(z,axis=1,keepdims=True)
    e=np.exp(z)
    return e/e.sum(axis=1,keepdims=True)

def fit(X,y):
    b=np.zeros((X.shape[1],3))
    Y=np.eye(3)[y]
    for _ in range(ITERATIONS):
        p=softmax(X@b)
        g=X.T@(p-Y)/len(X)+L2*b
        b-=LR*g
    return b

def devig(h,d,a):
    if min(h,d,a)<=1:return None
    x=np.array([1/h,1/d,1/a])
    return x/x.sum()

rows=[]
history=[]

for f in sorted(ROOT.glob("BRB_*.csv")):
    df=pd.read_csv(f)

    for _,r in df.iterrows():
        if str(r["status"]).lower()!="complete":
            continue

        odds=devig(
            float(r["odds_ft_home_team_win"]),
            float(r["odds_ft_draw"]),
            float(r["odds_ft_away_team_win"])
        )
        if odds is None: continue

        date=pd.to_datetime(int(r["timestamp"]),unit="s")
        home=str(r["home_team_name"])
        away=str(r["away_team_name"])
        hg=int(r["home_team_goal_count"])
        ag=int(r["away_team_goal_count"])

        rows.append({
            "date":date,"home":home,"away":away,
            "hg":hg,"ag":ag,"odds":odds,
            "result":0 if hg>ag else 2 if hg<ag else 1
        })

rows.sort(key=lambda x:x["date"])

def team_stats(hist,team,date):
    w=gf=ga=wt=0.0

    for r in hist:
        if r["home"]!=team and r["away"]!=team:
            continue

        days=max(0,(date-r["date"]).days)
        weight=math.exp(-DECAY*days/365.0)

        if r["home"]==team:
            f,a=r["hg"],r["ag"]
        else:
            f,a=r["ag"],r["hg"]

        w+=weight*(f>a)
        gf+=weight*f
        ga+=weight*a
        wt+=weight

    if wt==0:return None
    return w/wt,(gf-ga)/wt

X=[]
y=[]
meta=[]

for i,r in enumerate(rows):
    previous=rows[:i]

    hs=team_stats(previous,r["home"],r["date"])
    ass=team_stats(previous,r["away"],r["date"])

    if hs is None or ass is None:
        continue

    X.append([
        1.0,
        hs[0]-ass[0],
        hs[1]-ass[1],
        *r["odds"]
    ])
    y.append(r["result"])
    meta.append(r)

X=np.asarray(X,float)
y=np.asarray(y,int)

train_idx=np.array([m["date"].year<=2025 for m in meta])
test_idx=np.array([m["date"].year==2026 for m in meta])

Xtr,ytr=X[train_idx],y[train_idx]
Xte,yte=X[test_idx],y[test_idx]

b=fit(Xtr,ytr)
p=softmax(Xte@b)
pred=np.argmax(p,axis=1)

acc=np.mean(pred==yte)
ll=-np.mean(np.log(np.maximum(p[np.arange(len(yte)),yte],1e-15)))
actual=np.eye(3)[yte]
brier=np.mean(np.sum((p-actual)**2,axis=1))

print()
print("="*60)
print("SÉRIE B V3 FINAL OOS")
print("="*60)
print("TRAIN 2021-2025:",len(ytr))
print("OOS 2026:",len(yte))
print("RECENCY:",DECAY)
print("MARKET: DEVIG 1X2")
print()
print("ACCURACY:",acc)
print("LOG LOSS:",ll)
print("BRIER:",brier)
print()
print("ACTUAL DRAW:",np.sum(yte==1))
print("PREDICTED DRAW:",np.sum(pred==1))
print("CORRECT DRAW:",np.sum((pred==1)&(yte==1)))
print()
print("AVG PROB HOME:",p[:,0].mean())
print("AVG PROB DRAW:",p[:,1].mean())
print("AVG PROB AWAY:",p[:,2].mean())
print()
print("PREDICTED:",np.bincount(pred,minlength=3))
print("ACTUAL:",np.bincount(yte,minlength=3))
print()
print("COEFFICIENTS")
for i,name in enumerate([
    "INTERCEPT","RECENCY WIN_DIFF","RECENCY GOAL_DIFF",
    "MARKET_HOME","MARKET_DRAW","MARKET_AWAY"
]):
    print(name,"HOME=",b[i,0],"DRAW=",b[i,1],"AWAY=",b[i,2])

print()
print("Avaí/CRB 2026 ROWS:")
for m,pp in zip(np.array(meta,dtype=object)[test_idx],p):
    if "ava" in m["home"].lower() or "ava" in m["away"].lower() or "crb" in m["home"].lower() or "crb" in m["away"].lower():
        print(m["date"].date(),m["home"],"-",m["away"],"PROBS",pp)
