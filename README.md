# Курсы валют НБ РК

Хранилище дневных курсов Национального банка Казахстана.

## Данные

- Годовые CSV: `data/2022.csv`, `data/2023.csv`, `data/2024.csv`
- Ежедневные JSON: `data/daily/YYYY-MM-DD.json`

### Формат

CSV: `date,currency,rate` — `YYYY-MM-DD`, ISO-код валюты, курс в KZT за 1 единицу.

JSON: массив объектов `[{ "date":"YYYY-MM-DD", "currency":"USD", "rate":450.5900 }, ...]`.

Политика округления: 4 знака после запятой.

Источник: «Ежедневные официальные (рыночные) курсы валют» НБ РК.

Лицензия данных: as-is.

## CDN

```
https://cdn.jsdelivr.net/gh/<USER>/<REPO>@main/data/2024.csv
https://cdn.jsdelivr.net/gh/<USER>/<REPO>@main/data/daily/2024-12-31.json
```

