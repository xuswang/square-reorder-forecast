# Square Reorder Forecast

Inventory reorder forecasting for Square merchants. Pulls sales and stock data (read-only), predicts upcoming demand, and exports reorder lists.

## Features

- Square API integration (orders, inventory, catalog)
- Weighted daily sales + safety stock forecast
- Bilingual UI (English / 中文)
- Must-order Excel export with shipping notes
- Exclude not-for-sale catalog items

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 and enter your Square Access Token in the sidebar.

## CLI

```bash
cp .env.example .env   # optional
python main.py
```

## Security

- Access Token stays on your device and is sent only to Square's API
- Never commit `.env` (included in `.gitignore`)

## Copyright

© Xushen Wang. All rights reserved.
