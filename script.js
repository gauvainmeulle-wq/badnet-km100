// Coordonnées de La Cavalerie
const baseLat = 44.0983;
const baseLon = 3.0861;

// Distance Haversine
function distanceKm(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI/180;
    const dLon = (lon2 - lon1) * Math.PI/180;
    const a =
        Math.sin(dLat/2)**2 +
        Math.cos(lat1*Math.PI/180) *
        Math.cos(lat2*Math.PI/180) *
        Math.sin(dLon/2)**2;

    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// API BadNet (non documentée, mais fonctionnelle)
const API_URL = "https://badnet.fr/api/tournaments";

async function loadTournaments() {
    const container = document.getElementById("results");

    try {
        const response = await fetch(API_URL);
        const data = await response.json();

        const tournaments = data.items || [];

        const filtered = tournaments.filter(t => {
            if (!t.lat || !t.lon) return false;
            const d = distanceKm(baseLat, baseLon, t.lat, t.lon);
            return d <= 100;
        });

        if (filtered.length === 0) {
            container.innerHTML = "<p>Aucun tournoi trouvé dans ce rayon.</p>";
            return;
        }

        container.innerHTML = "";

        filtered.forEach(t => {
            const d = distanceKm(baseLat, baseLon, t.lat, t.lon).toFixed(1);

            const div = document.createElement("div");
            div.className = "tournament";
            div.innerHTML = `
                <h2>${t.name}</h2>
                <p><strong>Date :</strong> ${t.startDate} → ${t.endDate}</p>
                <p><strong>Ville :</strong> ${t.city}</p>
                <p><strong>Distance :</strong> ${d} km</p>
                <p><a href="https://badnet.fr/${t.url}" target="_blank">Voir le tournoi</a></p>
            `;
            container.appendChild(div);
        });

    } catch (err) {
        console.error(err);
        container.innerHTML = "<p>Erreur de récupération des données.</p>";
    }
}

loadTournaments();
