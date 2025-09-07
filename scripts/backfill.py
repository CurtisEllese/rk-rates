import os, sys, time, csv, datetime as dt
from common import fetch, prev_bd
BASE=os.path.dirname(os.path.dirname(__file__)); DATA=os.path.join(BASE,"data")
os.makedirs(DATA,exist_ok=True)
def upsert(year:int, items:list[dict]):
    path=os.path.join(DATA,f"{year}.csv"); store={}
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f:
            for r in csv.DictReader(f):
                store[(r["date"],(r["currency"] or "").upper())]=float(r["rate"])
    for it in items:
        store[(str(it["date"])[:10],(it["currency"] or "").upper())]=float(it["rate"])
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.writer(f); w.writerow(["date","currency","rate"])
        for (d,c),r in sorted(store.items()):
            w.writerow([d,c,f"{r:.4f}"])
def dates(a:dt.date,b:dt.date):
    if b<a: a,b=b,a
    d=a
    while d<=b:
        yield d; d+=dt.timedelta(days=1)
a=dt.datetime.strptime(sys.argv[1],"%Y-%m-%d").date()
b=dt.datetime.strptime(sys.argv[2],"%Y-%m-%d").date()
pick=set()
if len(sys.argv)>=4 and sys.argv[3].strip():
    pick={x.strip().upper() for x in sys.argv[3].split(",") if x.strip()}
total=0
for d in dates(a,b):
    if d.weekday()>=5: continue
    items=fetch(d)
    if not items:
        items=fetch(prev_bd(d))
        for it in items: it["date"]=d.strftime("%Y-%m-%d")
    if pick: items=[it for it in items if it["currency"] in pick]
    if items:
        upsert(d.year,items); total+=len(items); time.sleep(0.6)
print("rows:",total)
