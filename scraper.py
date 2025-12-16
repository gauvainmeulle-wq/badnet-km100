#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper BadNet (robuste)
- essaie de récupérer la page de résultats en ligne (SEARCH_URL)
- si la page en ligne ne contient pas d'items, tente de lire un fichier local 'badnet_search.html'
- parse les <a class="row" href="/tournoi/public?eventid=..."> et extrait nom, ville, date, lien
- géocode la ville via Nominatim (avec contrôles) et filtre par rayon (100 km) autour de La Cavalerie
- produit tournois.json
"""

import requests
from bs4 import BeautifulSoup
from geopy.distance import geodesic
import json
import time
import os
from urllib.parse import urljoin, urlparse, parse_qs

# --- CONFIG ---
BASE_POINT = (44.0189, 3.1017)  # La Cavalerie
RAYON_KM = 100
SEARCH_URL = "https://badnet.fr/recherche-competitions"  # remplace par l'URL exacte si tu l'as
LOCAL_HTML_FILE = "badnet_search.html"  # si tu colles la page HTML ici, le script l'utilisera
OUTPUT_JSON = "tournois.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# --- Fonctions utilitaires ---
def est_dans_rayon(lat, lon):
    try:
        distance = geodesic(BASE_POINT, (lat, lon)).km
        return distance <= RAYON_KM, round(distance)
    except Exception:
        return False, None

def safe_json_get(r):
    """Retourne JSON si valide, sinon None"""
    try:
        return r.json()
    except Exception:
        return None

def fetch_url(url):
    """GET simple avec header et timeout"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print("⚠️ Erreur HTTP lors du fetch :", e)
        return None

def parse_rows_from_html(html, base_url="https://badnet.fr"):
    """Parse les <a class='row' ...> et retourne une liste de dicts bruts"""
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("a.row")
    items = []
    for a in rows:
        try:
            href = a.get("href", "")
            # extraire eventid si présent
            eventid = None
            if "eventid=" in href:
                qs = parse_qs(urlparse(href).query)
                if "eventid" in qs:
                    eventid = qs["eventid"][0]
            # Nom
            nom_tag = a.select_one(".name")
            nom = nom_tag.get_text(" ", strip=True) if nom_tag else ""
            # Ville / location
            ville_tag = a.select_one(".location")
            ville = ville_tag.get_text(" ", strip=True) if ville_tag else ""
            # Date
            date_tag = a.select_one(".date")
            date_str = date_tag.get_text(" ", strip=True) if date_tag else ""
            # Lien complet
            lien = urljoin(base_url, href)
            items.append({
                "eventid": eventid,
                "nom": nom,
                "ville": ville,
                "dates": date_str,
                "lien": lien
            })
        except Exception as e:
            print("⚠️ Erreur parsing row :", e)
    return items

def geocode_city(city_name):
    """Geocode via Nominatim (retourne (lat, lon) ou (None, None)). Respecte le délai recommandé."""
    if not city_name:
        return None, None
    params = {"q": city_name + ", France", "format": "json", "limit": 1}
    try:
        r = requests.get(NOMINATIM_URL, params=params, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=15)
        if r.status_code != 200:
            return None, None
        data = safe_json_get(r)
        if not data:
            return None, None
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        # délai pour ne pas surcharger Nominatim
        time.sleep(1.1)
        return lat, lon
    except Exception:
        return None, None

# --- Logique principale ---
def scrape_from_web_or_local():
    print("⏳ Tentative de récupération depuis l'URL :", SEARCH_URL)
    html = fetch_url(SEARCH_URL)
    items = []
    if html:
        items = parse_rows_from_html(html, base_url=SEARCH_URL)
        print(f"ℹ️ {len(items)} éléments extraits depuis la page en ligne.")
    # si rien trouvé en ligne, essayer fichier local
    if not items:
        if os.path.exists(LOCAL_HTML_FILE):
            print(f"ℹ️ Aucun résultat utile en ligne — lecture du fichier local '{LOCAL_HTML_FILE}'.")
            with open(LOCAL_HTML_FILE, "r", encoding="utf-8") as f:
                html_local = f.read()
            items = parse_rows_from_html(html_local, base_url="https://badnet.fr")
            print(f"ℹ️ {len(items)} éléments extraits depuis le fichier local.")
        else:
            print("⚠️ Aucune donnée trouvée en ligne et aucun fichier local présent.")
    return items

def filter_and_geocode(items):
    resultats = []
    for it in items:
        ville = it.get("ville", "").strip()
        # nettoyage ville: enlever texte superflu (par ex. 'Strasbourg ' or with span)
        if ville:
            # tentatively try to use only first token before newline or multiple spaces
            ville_clean = ville.split("\n")[0].strip()
        else:
            ville_clean = ""
        lat, lon = None, None
        if ville_clean:
            lat, lon = geocode_city(ville_clean)
        # si géocodage échoue on peut choisir d'inclure ou non ; ici on inclut sans distance
        en_rayon = True
        distance_km = None
        if lat is not None and lon is not None:
            en_rayon, distance_km = est_dans_rayon(lat, lon)
        # on inclut si géolocal inconnu OR if in radius (pratique si ville non résolue)
        if (lat is None and lon is None) or en_rayon:
            result = {
                "eventid": it.get("eventid"),
                "nom": it.get("nom"),
                "dates": it.get("dates"),
                "ville": ville_clean,
                "distance_km": distance_km if distance_km is not None else "",
                "lien": it.get("lien")
            }
            resultats.append(result)
        else:
            # hors rayon -> ignorer
            pass
    return resultats

def main():
    items = scrape_from_web_or_local()
    if not items:
        print("❌ Aucun élément trouvé à parser.")
        # écrire fichier vide pour que widget n'explose pas
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
        print("✔ tournois.json généré vide.")
        return

    # filtrage + geocodage
    print("⏳ Géocodage et filtrage (peut prendre un moment si plusieurs lieux)...")
    final = filter_and_geocode(items)
    print(f"✔ {len(final)} tournois retenus après filtrage/ géocodage.")
    # écrire JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=4)
    print("🎉 JSON généré avec succès :", OUTPUT_JSON)

if __name__ == "__main__":
    main()

