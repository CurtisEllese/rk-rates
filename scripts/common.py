import datetime as dt, re
from lxml import html
import requests

HEADERS = {"User-Agent": "rk-rates-bot/1.0", "Accept": "text/html,application/xhtml+xml"}
BASE_URL = "https://nationalbank.kz/ru/exchangerates/ezhednevnye-oficialnye-rynochnye-kursy-valyut"


def ymd(d: dt.date) -> str:
    return d.strftime("%Y-%m-%d")


def prev_business_day(d: dt.date) -> dt.date:
    while d.weekday() >= 5:  # 5,6 = Sat, Sun
        d -= dt.timedelta(days=1)
    return d


def fetch_rates_html(date_obj: dt.date) -> list[dict]:
    """Возвращает [{"date":YYYY-MM-DD,"currency":ISO,"rate":float}, ...] за указанную дату."""
    url = f"{BASE_URL}?date={date_obj.strftime('%d.%m.%Y')}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    tree = html.fromstring(r.text)
    rows = tree.xpath("//table//tr")
    out = []
    for tr in rows:
        tds = [("".join(td.itertext())).strip() for td in tr.xpath(".//td")]
        if len(tds) < 2:
            continue
        code = None
        for cell in tds[:3]:
            token = re.sub(r"[^A-Za-z]", "", cell or "").upper()
            if 2 <= len(token) <= 5:
                code = token
                break
        if not code:
            continue
        rate = None
        for cell in reversed(tds):
            s = (cell or "").replace("\u00A0"," ").replace(" ","").replace(",", ".")
            try:
                rate = float(s)
                break
            except Exception:
                pass
        if rate is None:
            continue
        out.append({"date": ymd(date_obj), "currency": code, "rate": round(rate, 4)})

    # дедуп по (date,currency)
    uniq = {}
    for it in out:
        uniq[(it["date"], it["currency"])] = it["rate"]
    return [{"date": d, "currency": c, "rate": r} for (d, c), r in sorted(uniq.items())]
