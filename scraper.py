import requests
from bs4 import BeautifulSoup
from geopy.distance import geodesic
import json
import time

BASE_POINT = (44.0189, 3.1017)  # La Cavalerie
RAYON_KM = 100

URL = "https://badnet.fr/recherche-competitions"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest"
}

def distance_ok(ville):
    geo = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": ville, "format": "json"},
        headers={"User-Agent": "badnet-scraper"}
    ).json()

    if not geo:
        return None

    lat, lon = float(geo[0]["lat"]), float(geo[0]["lon"])
    d = geodesic(BASE_POINT, (lat, lon)).km
    return round(d, 1) if d <= RAYON_KM else None


def scrape_page(page):
    payload = {
        "ic_ajax": "1",
        "type_event": "70",
        "rayon": "100",
        "coming": "1",
        "page": page
    }

    r = requests.post(URL, data=payload, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.select("a.row")
    results = []

    for row in rows:
        nom = row.select_one(".name").get_text(strip=True)
        ville = row.select_one(".location").get_text(strip=True)
        date = row.select_one(".date").get_text(strip=True)
        lien = "https://badnet.fr" + row["href"]

        dist = distance_ok(ville)
        if dist is not None:
            results.append({
                "nom": nom,
                "ville": ville,
                "date": date,
                "distance_km": dist,
                "lien": lien
            })

    return results


def scrape_all():
    all_results = []

    for page in range(0, 6):  # 6 pages max (évite bannissement)
        print(f"📄 Page {page+1}")
        data = scrape_page(page)
        if not data:
            break
        all_results.extend(data)
        time.sleep(1)

    return all_results


if __name__ == "__main__":
    print("⏳ Scraping en cours...")
    tournois = scrape_all()

    with open("tournois.json", "w", encoding="utf-8") as f:
        json.dump(tournois, f, ensure_ascii=False, indent=2)

    print(f"🎉 {len(tournois)} tournois trouvés")


