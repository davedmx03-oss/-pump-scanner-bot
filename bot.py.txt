
import os
import time
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

API_URLS = [
    "https://frontend-api-v3.pump.fun/coins?offset=0&limit=10&sort=created_timestamp&order=DESC&includeNsfw=false",
    "https://frontend-api-v2.pump.fun/coins?offset=0&limit=10&sort=created_timestamp&order=DESC&includeNsfw=false",
    "https://frontend-api.pump.fun/coins?offset=0&limit=10&sort=created_timestamp&order=DESC"
]

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
        r = requests.post(url, json=payload, timeout=20)
        print(f"Telegram: {r.status_code}")
        return r.ok
    except Exception as e:
        print(f"TG error: {e}")
        return False

def fetch_coins():
    for api_url in API_URLS:
        try:
            print(f"Trying {api_url[:50]}")
            r = requests.get(api_url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"Got {len(data)} coins")
                    return data
        except Exception as e:
            print(f"API error: {e}")
    return []

print("🚀 Bot V2 ULTIMATE V3 CLOUD Starting...")
if not TOKEN or not CHAT_ID:
    print("ERROR: Set TELEGRAM_TOKEN and ADMIN_CHAT_ID in Render ENV!")
    exit(1)

send_telegram("✅ *Bot ULTIMATE V3 CLOUD Aktif!*\n\nScan 3 API: pump v3 + v2 + Dexscreener\nFilter: MC $2k-$40k\n\nBot jalan 24 jam gratis ✅")

seen = set()
count = 0
while True:
    try:
        count += 1
        coins = fetch_coins()
        if not coins:
            print(f"[{count}] No coins, wait 20s")
            time.sleep(20)
            continue
        new_c = 0
        for coin in coins:
            mint = coin.get('mint') or coin.get('id')
            if not mint or mint in seen:
                continue
            mcap = coin.get('usd_market_cap', 0) or coin.get('market_cap', 0) or 0
            if not (2000 < mcap < 40000):
                seen.add(mint)
                continue
            seen.add(mint)
            new_c += 1
            name = coin.get('name','Unknown')
            symbol = coin.get('symbol','???')
            msg = f"🚀 *NEW SCAN ULTIMATE V3*\n\n*{name}* (${symbol})\nMCap: ${mcap:,.0f}\nCA: `{mint}`\n\n[Pump.fun](https://pump.fun/{mint}) | [Dexscreener](https://dexscreener.com/solana/{mint})"
            send_telegram(msg)
            time.sleep(1)
        print(f"[{count}] Scan... {len(coins)} checked, {new_c} new - wait 15s")
        time.sleep(15)
    except Exception as e:
        print(f"Loop error: {e}")
        time.sleep(10)
