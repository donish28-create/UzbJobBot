
# UzbJobBot (Aiogram v3) — v2

Job seeker / employer bot for Uzbekistan.

## Features
- Uzbek (Latin) UI
- Flows: **Ish kerak**, **Ishchi kerak**
- 20+ categories + "Boshqa yo‘nalish" with smart normalization
- Region picker incl. **Butun Oʻzbekiston bo‘yicha**
- **Contact visibility choice** (show/hide phone in channel posts)
- Auto-post to channel (`CHANNEL_ID`), compact admin notifications
- SQLite storage

## Env (.env)
```
BOT_TOKEN=REPLACE_WITH_YOUR_TOKEN
ADMIN_ID=1290927452
CHANNEL_ID=@UzbJobElonlar
```

## Run
```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Deploy to Render (GitHub route)
1) Create a GitHub repo and push this folder.
2) On Render: **New → Web Service → Public Git Repository** → paste repo URL.
3) Set Environment Variables above.
4) Start command: `python main.py`
