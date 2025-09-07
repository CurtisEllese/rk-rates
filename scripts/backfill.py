import os, sys, time, json, csv, datetime as dt
from common import fetch_rates_html, prev_business_day

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DAILY_DIR = os.path.join(DATA_DIR, "daily")
os.makedirs(DAILY_DIR, exist_ok=True)

def upsert_year_csv(year: int, items: list[dict]) -> None:
    path = os.path.join(DATA_DIR, f"{year}.csv")
    existing = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            rd = csv.DictReader(f)
            for row in rd:
                existing[(row["date"], row["currency"].upper())] = float(row["rate"])
    for it in items:
        key = (it["date"][:10], it["currency"].upper())
        existing[key] = float(it["rate"])
    with open(path, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["date","currency","rate"])
        for (d, c), r in sorted(existing.items()):
            wr.writerow([d, c, f"{r:.4f}"])

def daterange(a: dt.date, b: dt.date):
    if b < a:
        a, b = b, a
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)

def main():
    # Аргументы: YYYY-MM-DD YYYY-MM-DD (включительно)
    if len(sys.argv) < 3:
        print("Usage: python scripts/backfill.py 2022-01-01 2024-12-31")
        sys.exit(1)
    a = dt.datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    b = dt.datetime.strptime(sys.argv[2], "%Y-%m-%d").date()

    total = 0
    for d in daterange(a, b):
        if d.weekday() >= 5:  # пропускаем выходные
            continue
        items = fetch_rates_html(d)
        if not items:
            # если праздники/нет страницы — попробуем предыдущий рабочий
            items = fetch_rates_html(prev_business_day(d))
        if not items:
            print("skip", d)
            continue
        # daily
        os.makedirs(DAILY_DIR, exist_ok=True)
        with open(os.path.join(DAILY_DIR, f"{d.strftime('%Y-%m-%d')}.json"), "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        # year
        upsert_year_csv(d.year, items)
        total += len(items)
        # аккуратный throttling, чтобы не долбить сайт
        time.sleep(0.7)
    print("Backfill done, rows:", total)

if __name__ == "__main__":
    main()
