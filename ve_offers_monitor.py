import os
import json
import time
import hashlib
import requests
from datetime import datetime

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "300"))

SOURCES = [
    {"name": "LeBonCoin VE", "url": "https://www.leboncoin.fr/recherche?category=2&u_car_fuel=5", "type": "leboncoin"},
    {"name": "AutoScout24 VE", "url": "https://www.autoscout24.fr/lst?fuel=E", "type": "autoscout24"}
]

seen_offers = set()


def send_slack_alert(offer):
    if not SLACK_WEBHOOK_URL:
        print("WARNING: SLACK_WEBHOOK_URL non configure")
        return
    message = {
        "text": ":zap: *Nouvelle offre VE detectee!*",
        "attachments": [{"color": "#36a64f", "fields": [
            {"title": "Source", "value": offer.get("source", "N/A"), "short": True},
            {"title": "Titre", "value": offer.get("title", "N/A"), "short": True},
            {"title": "Prix", "value": offer.get("price", "N/A"), "short": True},
            {"title": "Localisation", "value": offer.get("location", "N/A"), "short": True},
        ], "footer": f"VE Monitor | {datetime.now().strftime('%d/%m/%Y %H:%M')}", "title_link": offer.get("url", "")}]
    }
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=message, timeout=10)
        response.raise_for_status()
        print(f"[OK] Alerte Slack envoyee: {offer.get('title', 'N/A')}")
    except Exception as e:
        print(f"[ERROR] Echec envoi Slack: {e}")


def fetch_source(source):
    headers = {"User-Agent": "Mozilla/5.0"}
    offers = []
    try:
        response = requests.get(source["url"], headers=headers, timeout=15)
        response.raise_for_status()
        print(f"[OK] Fetched {source['name']}: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Fetch {source['name']}: {e}")
    return offers


def get_offer_id(offer):
    key = f"{offer.get('title', '')}{offer.get('price', '')}{offer.get('url', '')}"
    return hashlib.md5(key.encode()).hexdigest()


def check_offers():
    global seen_offers
    new_count = 0
    for source in SOURCES:
        print(f"[INFO] Verification de {source['name']}...")
        offers = fetch_source(source)
        for offer in offers:
            offer_id = get_offer_id(offer)
            if offer_id not in seen_offers:
                seen_offers.add(offer_id)
                send_slack_alert(offer)
                new_count += 1
    print(f"[INFO] Cycle termine. {new_count} nouvelle(s) offre(s) detectee(s).")
    return new_count


def startup_test():
    if not SLACK_WEBHOOK_URL:
        print("WARNING: SLACK_WEBHOOK_URL non configure")
        return
    message = {"text": f":rocket: *VE Offers Monitor demarre!* | Intervalle: {CHECK_INTERVAL}s | Sources: {len(SOURCES)} | {datetime.now().strftime('%d/%m/%Y %H:%M')}"}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=message, timeout=10)
        response.raise_for_status()
        print("[OK] Message de demarrage envoye sur Slack")
    except Exception as e:
        print(f"[ERROR] Echec message demarrage: {e}")


def main():
    print("VE Offers Monitor - Demarrage")
    startup_test()
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Lancement du cycle...")
            check_offers()
            print(f"Prochaine verification dans {CHECK_INTERVAL}s...")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("Arret.")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
