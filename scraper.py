import requests
from bs4 import BeautifulSoup
from geopy.distance import geodesic
import json

BASE_POINT = (44.0189, 3.1017)  # La Cavalerie
RAYON_KM = 100
URL_TOURNOIS = "https://badnet.fr/recherche-competitions"

def est_dans_rayon(lat, lon):
    return geodesic(BASE_POINT, (lat, lon)).km <= RAYON_KM

def scrape_tournois():
    r = requests.get(URL_TOURNOIS)
    soup = BeautifulSoup(r.text, "html.parser")
    lignes = soup.select(".competition-row")  # adapter si nécessaire

    resultats = []
    for row in lignes:
        nom = row.select_one(".nom").get_text(strip=True)
        dates = row.select_one(".dates").get_text(strip=True)
        ville = row.select_one(".ville").get_text(strip=True)
        lien = row.select_one("a")["href"]

        geo = requests.get("https://nominatim.openstreetmap.org/search",
                           params={"q": ville, "format": "json"}).json()

        if geo:
            lat = float(geo[0]["lat"])
            lon = float(geo[0]["lon"])
            if est_dans_rayon(lat, lon):
                resultats.append({
                    "nom": nom,
                    "dates": dates,
                    "ville": ville,
                    "distance_km": round(geodesic(BASE_POINT, (lat, lon)).km),
                    "lien": lien
                })
    return resultats

if __name__ == "__main__":
    tournois = scrape_tournois()
    with open("tournois.json", "w", encoding="utf-8") as f:
        json.dump(tournois, f, ensure_ascii=False, indent=4)
    print("JSON généré avec succès")
