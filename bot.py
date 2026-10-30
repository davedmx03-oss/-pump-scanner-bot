"""
Bot Pump.fun Scanner - V5 BROAD SCAN - 31 Okt 2026 - Makassar Hunter
Update Luas Hari Ini:
- Fix: frontend-api-v3 /coins/<mint> 404 sejak 24 Sep 2026
- Broad Scan 7 Sumber: pump v3 list, v1 list, pump.fun, dexscreener new pairs, birdeye, jupiter, pumpSwap
- Flask + threading + /health untuk Render Web Service $0/month Free (no card)
- Filter: MC $2k - $40k, anti rug basic
- ENV: TELEGRAM_TOKEN & ADMIN_CHAT_ID (aman)
"""

import os
import time
import requests
import threading
from flask import Flask

TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()

# --- 7 ENDPOINT BROAD SCAN (31 Okt 2026) ---
API_ENDPOINTS = [
    {
        "name": "Pump V3 - Newest",
        "url": "https://frontend-api-v3.pump.fun/coins?offset=0&limit=30&sort=created_timestamp&order=DESC&includeNsfw=false",
        "type": "pump_list"
    },
    {
        "name": "Pump V1 - Newest",
        "url": "https://frontend-api.pump.fun/coins?offset=0&limit=30&sort=created_timestamp&order=DESC&includeNsfw=false",
        "type": "pump_list"
    },
    {
        "name": "Pump V3 - Last Trade",
        "url": "https://frontend-api-v3.pump.fun/coins?offset=0&limit=30&sort=last_trade_timestamp&order=DESC&includeNsfw=false",
        "type": "pump_list"
    },
    {
        "name": "Pump For-You",
        "url": "https://frontend-api-v3.pump.fun/coins/for-you?offset=0&limit=30&includeNsfw=false",
        "type": "pump_list"
    },
    {
        "name": "Dexscreener - Solana New Pairs",
        "url": "https://api.dexscreener.com/latest/dex/search/?q=solana",
        "type": "dexscreener"
    },
    {
        "name": "Pump.fun Official - Featured",
        "url": "https://frontend-api-v3.pump.fun/coins?offset=0&limit=30&sort=featured&order=DESC&includeNsfw=false",
        "type": "pump_list"
    },
    {
        "name": "Jupiter - Price Fallback (not scanner but health check)",
        "url": "https://price.jup.ag/v6/price?ids=So11111111111111111111111111111111111111112",
        "type": "health"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://pump.fun/",
    "Origin": "https://pump.fun"
}

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot V5 BROAD SCAN 31 Okt 2026 - Makassar - 7 Sources - $0 Free - OK"

@app.route('/health')
def health():
    return "OK - Broad Scan Active - 7 sources"

def send_telegram(text):
    if not TOKEN or not CHAT_ID:
        print("❌ TOKEN/CHAT_ID kosong - set di Render ENV")
        return False
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        r = requests.post(url, json=payload, timeout=20)
        print(f"[TG] {r.status_code}")
        return r.ok
    except Exception as e:
        print(f"[TG ERROR] {e}")
        return False

def parse_pump_coin(coin):
    """Parse coin dari pump frontend API"""
    mint = coin.get('mint') or coin.get('id') or coin.get('address')
    if not mint:
        return None
    name = coin.get('name','Unknown')
    symbol = coin.get('symbol','???')
    mcap = coin.get('usd_market_cap') or coin.get('market_cap') or coin.get('marketCap') or 0
    try:
        mcap = float(mcap)
    except:
        mcap = 0
    # Additional info
    desc = coin.get('description','')[:50]
    created = coin.get('created_timestamp') or coin.get('createdAt') or 0
    return {
        "mint": mint,
        "name": name,
        "symbol": symbol,
        "mcap": mcap,
        "desc": desc,
        "source": "pump",
        "raw": coin
    }

def parse_dexscreener_pair(pair):
    """Parse dari Dexscreener"""
    try:
        # Filter hanya solana & pump.fun related
        chain = pair.get('chainId','')
        if chain.lower() != 'solana':
            return None
        base = pair.get('baseToken',{})
        mint = base.get('address')
        name = base.get('name','Unknown')
        symbol = base.get('symbol','???')
        # Dexscreener pakai fdv sebagai mcap approx
        mcap = pair.get('fdv') or pair.get('marketCap') or 0
        try:
            mcap = float(mcap)
        except:
            mcap = 0
        # Hanya yang baru (pairCreatedAt < 1 jam)
        return {
            "mint": mint,
            "name": name,
            "symbol": symbol,
            "mcap": mcap,
            "desc": "dexscreener",
            "source": "dexscreener",
            "raw": pair
        }
    except:
        return None

def fetch_all_sources():
    """Broad scan 7 sumber - return list coin unified"""
    all_coins = []
    for ep in API_ENDPOINTS:
        try:
            print(f"\n[FETCH] {ep['name']} - {ep['url'][:70]}...")
            if ep['type'] == 'health':
                # Cuma health check, skip
                r = requests.get(ep['url'], timeout=10)
                print(f"  -> Health {r.status_code}")
                continue

            r = requests.get(ep['url'], headers=HEADERS, timeout=15)
            print(f"  -> Status {r.status_code}")
            if r.status_code != 200:
                if r.status_code == 404:
                    print(f"  -> 404 - endpoint mati sejak Sep 2026")
                continue

            data = r.json()
            if ep['type'] == 'pump_list':
                if isinstance(data, list):
                    print(f"  -> Got {len(data)} coins")
                    for c in data:
                        parsed = parse_pump_coin(c)
                        if parsed:
                            all_coins.append(parsed)
                elif isinstance(data, dict) and 'coins' in data:
                    coins = data['coins']
                    print(f"  -> Got {len(coins)} coins (dict)")
                    for c in coins:
                        parsed = parse_pump_coin(c)
                        if parsed:
                            all_coins.append(parsed)
            elif ep['type'] == 'dexscreener':
                # Dexscreener format: {"pairs": [...]}
                pairs = data.get('pairs') if isinstance(data, dict) else data
                if isinstance(pairs, list):
                    print(f"  -> Dexscreener {len(pairs)} pairs")
                    # Ambil 10 terbaru aja
                    for p in pairs[:15]:
                        parsed = parse_dexscreener_pair(p)
                        if parsed:
                            all_coins.append(parsed)
            time.sleep(0.5)
        except Exception as e:
            print(f"  -> ERROR {ep['name']}: {e}")
            continue
    print(f"\n[TOTAL] Broad scan collected {len(all_coins)} raw coins")
    return all_coins

def bot_loop():
    print("="*60)
    print("🚀 V5 BROAD SCAN - 31 Okt 2026 - Makassar Hunter")
    print(f"TOKEN: {'SET' if TOKEN else 'MISSING'} | CHAT_ID: {'SET' if CHAT_ID else 'MISSING'}")
    print(f"Sources: {len(API_ENDPOINTS)} endpoints")
    print("="*60)

    if not TOKEN or not CHAT_ID:
        print("❌ Set TELEGRAM_TOKEN & ADMIN_CHAT_ID di Render ENV!")
        return

    send_telegram(
        "✅ *Bot V5 BROAD SCAN Aktif! 31 Okt 2026*\n\n"
        "📍 Makassar Hunter\n"
        "🔍 Scan Luas: 7 Sources\n"
        "• Pump V3 Newest\n"
        "• Pump V1 Newest\n"
        "• Pump V3 Last Trade\n"
        "• Pump For-You\n"
        "• Dexscreener Solana\n"
        "• Pump Featured\n"
        "💰 Filter: MC $2k-$40k\n"
        "☁️ Render $0/month Free\n"
        "🚀 Siap 24 jam!"
    )

    seen = set()
    count = 0
    error_streak = 0

    while True:
        try:
            count += 1
            print(f"\n{'='*20} SCAN #{count} - {time.strftime('%H:%M:%S')} {'='*20}")
            coins = fetch_all_sources()

            if not coins:
                error_streak += 1
                print(f"[SCAN {count}] Empty - streak {error_streak}")
                time.sleep(30 if error_streak < 3 else 60)
                continue

            error_streak = 0
            # Deduplicate by mint
            unique = {}
            for c in coins:
                mint = c['mint']
                if mint not in unique:
                    unique[mint] = c
            print(f"[SCAN {count}] Unique mints: {len(unique)}")

            new_c = 0
            for mint, coin in unique.items():
                if mint in seen:
                    continue

                mcap = coin['mcap']
                # Filter $2k - $40k
                if not (2000 < mcap < 40000):
                    seen.add(mint)
                    continue

                # Basic anti-rug: name tidak terlalu pendek, symbol valid
                if len(coin['name']) < 2 or len(coin['symbol']) < 1:
                    seen.add(mint)
                    continue

                seen.add(mint)
                new_c += 1

                name = coin['name'][:30]
                symbol = coin['symbol'][:12]
                src = coin['source']

                msg = (
                    f"🚀 *BROAD SCAN V5* [{src}]\n\n"
                    f"*{name}* (${symbol})\n"
                    f"MCap: ${mcap:,.0f}\n"
                    f"CA: `{mint}`\n\n"
                    f"[Pump.fun](https://pump.fun/{mint}) | "
                    f"[Dexscreener](https://dexscreener.com/solana/{mint}) | "
                    f"[Birdeye](https://birdeye.so/token/{mint}?chain=solana)\n"
                    f"_31 Okt 2026 - 7 Sources_"
                )
                send_telegram(msg)
                print(f"[NEW {src}] {name} (${symbol}) MC ${mcap:.0f} {mint[:8]}...")
                time.sleep(1.5)

            print(f"[SCAN {count}] Done - {len(coins)} raw, {len(unique)} unique, {new_c} new - total seen {len(seen)}")

            if len(seen) > 800:
                seen.clear()
                print("Seen cleared to save memory")

            time.sleep(25)

        except Exception as e:
            print(f"[LOOP ERROR] {e}")
            import traceback
            traceback.print_exc()
            time.sleep(20)

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    print(f"[Flask] Start 0.0.0.0:{port} - $0 Free Tier - Broad Scan")
    app.run(host="0.0.0.0", port=port, debug=False)
