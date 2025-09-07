import datetime as dt
import re
from lxml import html
import requests

HEADERS = {"User-Agent": "rk-rates-bot/1.0", "Accept": "text/html,application/xhtml+xml"}
BASE_URL = "https://nationalbank.kz/ru/exchangerates/ezhednevnye-oficialnye-rynochnye-kursy-valyut"

def to_date10(value):
    if isinstance(value, dt.date):
        return value.strftime("%Y-%m-%d")
    s = str(value)[:10]
    return s

def prev_business_day(d: dt.date) -> dt.date:
    while d.weekday() >= 5:  # 5=Sat, 6=Sun
        d -= dt.timedelta(days=1)
    return d

def fetch_rates_html(date_obj: dt.date) -> list[dict]:
    """
    Парсит HTML-страницу НБРК для указанной даты (формат в query: DD.MM.YYYY).
    Возвращает список словарей: {"date":YYYY-MM-DD, "currency":ISO, "rate":float}
    """
    d_str = date_obj.strftime("%d.%m.%Y")
    url = f"{BASE_URL}?date={d_str}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    tree = html.fromstring(r.text)

    # Ищем таблицу с курсами; заберём все строки <tr>
    rows = tree.xpath("//table//tr")
    out = []
    for tr in rows:
        tds = [("".join(td.itertext())).strip() for td in tr.xpath(".//td")]
        if len(tds) < 2:
            continue
        # Попробуем вытащить ISO-код (USD/EUR/RUB/…)
        code = None
        for cell in tds[:3]:
            token = re.sub(r"[^A-Za-z]", "", cell).upper()
            if 2 <= len(token) <= 5:
                code = token
                break
        if not code:
            continue
        # Попробуем вытащить число курса (берём последнее поле справа, которое парсится в float)
        rate = None
        for cell in reversed(tds):
            s = cell.replace("\u00A0", " ").replace(" ", "").replace(",", ".")
            try:
                rate = float(s)
                break
            except Exception:
                pass
        if rate is None:
            continue
        out.append({"date": date_obj.strftime("%Y-%m-%d"), "currency": code, "rate": round(rate, 4)})
    # Удалим дубликаты по (date,currency), оставив последнее значение
    uniq = {}
    for it in out:
        uniq[(it["date"], it["currency"])] = it["rate"]
    return [{"date": d, "currency": c, "rate": r} for (d, c), r in sorted(uniq.items())]
