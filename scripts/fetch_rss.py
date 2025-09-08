import datetime as dt, time, os, sys, csv, re, xml.etree.ElementTree as ET
import requests

UA = {"User-Agent":"rk-rates-bot/1.0","Accept":"application/xml","Accept-Language":"ru,en;q=0.9"}
BASE = "https://nationalbank.kz/rss/get_rates.cfm?fdate={}"

def ddmmyyyy(d: dt.date) -> str:
    return d.strftime("%d.%m.%Y")

def ymd(d: dt.date) -> str:
    return d.strftime("%Y-%m-%d")

def prev_bd(d: dt.date) -> dt.date:
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return d

def fetch_day(d: dt.date):
    """Возвращает список dict: {'date','currency','rate'} из RSS на дату d."""
    url = BASE.format(ddmmyyyy(d))
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    # NBK RSS — это <rates><item>...</item>...</rates>
    root = ET.fromstring(r.content)
    out = []
    for item in root.findall(".//item"):
        # пытаемся взять код валюты
        # часто встречаются: <title>USD</title> <index>USD</index> <fullname>...</fullname>
        code_texts = []
        for tag in ("index","title","charcode","code"):
            el = item.find(tag)
            if el is not None and (el.text or "").strip():
                code_texts.append(el.text.strip())
        code = None
        for t in code_texts:
            t = re.sub(r"[^A-Za-z]", "", t or "").upper()
            if re.fullmatch(r"[A-Z]{3}", t):
                code = t
                break
        if not code:
            # иногда код может быть в title вроде "1 USD"
            all_text = " ".join([(item.find(t).text or "") for t in ("title","fullname","description") if item.find(t) is not None])
            m = re.search(r"\b([A-Za-z]{3})\b", all_text or "")
            if m: code = m.group(1).upper()
        if not code or code == "KZT":
            continue

        # парсим курс — часто в <description>, иногда в <value>
        rate = None
        for tag in ("description","value","target","current"):
            el = item.find(tag)
            if el is not None and (el.text or "").strip():
                s = el.text.replace("\xa0"," ").replace(" ","").replace(",",".")
                try:
                    rate = float(re.search(r"[-+]?\d+(?:\.\d+)?", s).group())
                    break
                except Exception:
                    pass
        if rate is None:
            # fallback: ищем первое число в конкатенации полей
            s = " ".join([(item.find(t).text or "") for t in ("description","title","fullname") if item.find(t) is not None])
            s = s.replace("\xa0"," ").replace(" ","").replace(",",".")
            m = re.search(r"[-+]?\d+(?:\.\d+)?", s)
            if m:
                rate = float(m.group())

        if rate is None:
            continue

        out.append({"date": ymd(d), "currency": code, "rate": round(rate,4)})
    # дедуп по (date,currency)
    seen = {}
    for it in out:
        seen[(it["date"], it["currency"])] = it["rate"]
    return [{"date": d, "currency": c, "rate": r} for (d,c),r in sorted(seen.items())]

def upsert_csv(year: int, items: list[dict]):
    path = os.path.join("data", f"{year}.csv")
    store = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                store[(r["date"], (r["currency"] or "").upper())] = float(r["rate"])
    for it in items:
        d = str(it["date"])[:10]; c = (it["currency"] or "").upper(); v = float(it["rate"])
        store[(d,c)] = v
    os.makedirs("data", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["date","currency","rate"])
        for (d,c),v in sorted(store.items()):
            w.writerow([d,c,f"{v:.4f}"])

if __name__ == "__main__":
    import sys
    a = dt.datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    b = dt.datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
    pick = set()
    if len(sys.argv) >= 3 and len(sys.argv) == 4 and sys.argv[3].strip():
        pick = {x.strip().upper() for x in sys.argv[3].split(",") if x.strip()}
    if b < a: a, b = b, a

    total = 0
    cur = a
    while cur <= b:
        if cur.weekday() < 5:
            items = fetch_day(cur)
            # если пусто (праздник), возьмём предыдущий рабочий и отметим текущей датой
            if not items:
                alt = prev_bd(cur - dt.timedelta(days=1))
                alt_items = fetch_day(alt)
                items = [{"date": (cur.strftime("%Y-%m-%d")), "currency": it["currency"], "rate": it["rate"]} for it in alt_items]
            if pick:
                items = [it for it in items if it["currency"] in pick]
            if items:
                upsert_csv(cur.year, items)
                total += len(items)
            time.sleep(0.4)  # мягкий throttle
        cur += dt.timedelta(days=1)
    print(f"rows: {total}")
