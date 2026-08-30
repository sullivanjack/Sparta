let historicalSeasons;

function renderHistoricalYear(year) {
  const season = historicalSeasons.find(item => item.year === year);
  if (!season) return;
  const lowScore = season.standings[0].net_total;
  document.querySelector("#historical-year-title").textContent = `${year} Leaderboard`;
  document.querySelector("#historical-leaderboard").innerHTML = season.standings.map(player => `<tr>
    <td class="muted">${player.rank}</td>
    <td><strong>${player.name}</strong>${player.net_total === lowScore ? '<span class="historical-leader">Champion</span>' : ""}</td>
    <td class="money"><strong>${player.net_total}</strong></td>
  </tr>`).join("");
}

async function init() {
  try {
    const response = await fetch("data/sparta.json");
    if (!response.ok) throw new Error(`Data request failed (${response.status})`);
    const data = await response.json();
    historicalSeasons = data.historical_seasons;
    if (!historicalSeasons?.length) throw new Error("No historical scores were found.");
    const requestedYear = Number(new URLSearchParams(location.search).get("year"));
    const year = historicalSeasons.some(season => season.year === requestedYear)
      ? requestedYear
      : historicalSeasons[0].year;
    renderHistoricalYear(year);
  } catch (error) {
    document.querySelector("#historical-content").innerHTML = `<section class="section shell"><div class="error">Could not load the historical archive: ${error.message}</div></section>`;
  }
}

init();
