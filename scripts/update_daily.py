import os, json, csv, datetime as dt
from common import fetch_rates_html, prev_business_day, ymd

BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data")
DAILY = os.path.join(DATA, "daily")
os.makedirs(DAILY, exist_ok=True)

def upsert(year: int, items: list[dict]) -> None:
    path = os.path.join(DATA, f"{year}.csv")
    store = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                store[(r["date"], (r["currency"] or "").upper())] = float(r["rate"])
    for it in items:
        store[(str(it["date"])[:10], (it["currency"] or "").upper())] = float(it["rate"])
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["date","currency","rate"])
        for (d, c), r in sorted(store.items()):
            w.writerow([d, c, f"{r:.4f}"])

def main():
    today = dt.date.today()
    d = prev_business_day(today)
    items = fetch_rates_html(d)
    if not items:
        return
    with open(os.path.join(DAILY, f"{ymd(d)}.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    upsert(d.year, items)
    print(f"Updated {d}: {len(items)} rates")

if __name__ == "__main__":
    main()
