import os, json, csv, datetime as dt
from common import fetch_rates_html, prev_business_day

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DAILY_DIR = os.path.join(DATA_DIR, "daily")
os.makedirs(DAILY_DIR, exist_ok=True)

def upsert_year_csv(year: int, items: list[dict]) -> int:
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
    return len(items)

def main():
    today = dt.date.today()
    d = prev_business_day(today)  # если выходной, берём последнюю рабочую дату
    items = fetch_rates_html(d)
    if not items:
        print("No rates fetched for", d)
        return
    # daily JSON
    daily_path = os.path.join(DAILY_DIR, f"{d.strftime('%Y-%m-%d')}.json")
    with open(daily_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    # year CSV
    upsert_year_csv(d.year, items)
    print(f"Updated {d}: {len(items)} rates")

if __name__ == "__main__":
    main()
