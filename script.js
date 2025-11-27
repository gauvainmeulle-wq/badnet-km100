fetch("tournois.json")
  .then(response => response.json())
  .then(data => {
    const container = document.getElementById("tournois-badnet");

    if (!data.length) {
      container.innerHTML = "<p>Aucun tournoi trouvé dans un rayon de 100 km.</p>";
      return;
    }

    let html = "<h2>Tournois autour de La Cavalerie (100 km)</h2><ul style='list-style:none;padding:0'>";
    data.forEach(t => {
      html += `
        <li style="margin-bottom:15px;padding:10px;border:1px solid #ccc;border-radius:8px;">
          <strong>${t.nom}</strong><br>
          📅 ${t.dates}<br>
          📍 ${t.ville} — ${t.distance_km} km<br>
          <a href="${t.lien}" target="_blank" 
             style="margin-top:5px;display:inline-block;padding:6px 12px;background:#1f7ad1;color:white;border-radius:5px;text-decoration:none;">
             Voir sur BadNet
          </a>
        </li>`;
    });
    html += "</ul>";
    container.innerHTML = html;
  })
  .catch(err => {
    console.error(err);
    document.getElementById("tournois-badnet").innerHTML =
      "<p>Erreur de chargement des tournois.</p>";
  });

