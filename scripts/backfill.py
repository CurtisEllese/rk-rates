import os, sys, time, csv, datetime as dt
from common import fetch_rates_html, prev_business_day, ymd

BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

def upsert(year: int, items: list[dict]) -> int:
    path = os.path.join(DATA, f"{year}.csv")
    store = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                store[(r["date"], (r["currency"] or "").upper())] = float(r["rate"])
    for it in items:
        d = str(it["date"] )[:10]
        c = (it["currency"] or "").upper()
        r = float(it["rate"])
        store[(d, c)] = r
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["date","currency","rate"])
        for (d, c), r in sorted(store.items()):
            w.writerow([d, c, f"{r:.4f}"])
    return len(items)

def daterange(a: dt.date, b: dt.date):
    if b < a: a, b = b, a
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)

def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/backfill.py 2024-01-01 2024-12-31 [USD,EUR,RUB]")
        sys.exit(1)
    a = dt.datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    b = dt.datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
    pick = set()
    if len(sys.argv) >= 4:
        pick = {x.strip().upper() for x in sys.argv[3].split(",") if x.strip()}
    total = 0
    for d in daterange(a, b):
        if d.weekday() >= 5:   # пропускаем выходные, там официальных значений нет
            continue
        items = fetch_rates_html(d)
        if not items:
            # на случай праздника — возьмём ближайший рабочий назад
            items = fetch_rates_html(prev_business_day(d))
            for it in items:
                it["date"] = ymd(d)  # фиксируем курс на отчётную дату
        if pick:
            items = [it for it in items if it["currency"] in pick]
        if items:
            upsert(d.year, items)
            total += len(items)
            time.sleep(0.6)  # бережный throttle
    print("backfill rows:", total)


if __name__ == "__main__":
    main()
