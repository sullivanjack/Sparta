const playerLink = name => `player.html?name=${encodeURIComponent(name)}`;
let data;

function renderChampions() {
  document.querySelector("#champions-grid").innerHTML = data.seasons.map(season => {
    const champion = season.standings[0];
    const dailyScores = Object.entries(champion.day_scores)
      .sort(([left], [right]) => Number(left) - Number(right))
      .map(([day, score]) => `<span><small>Day ${day}</small><strong>${score}</strong></span>`)
      .join("");
    return `<article class="champion-card">
      <a class="champion-year" href="year.html?year=${season.year}">${season.year}</a>
      <div class="champion-name"><span>Champion</span><a href="${playerLink(champion.name)}">${champion.name}</a></div>
      <div class="champion-scores">${dailyScores}<span class="champion-total"><small>Total net</small><strong>${champion.total_net}</strong></span></div>
      <a class="champion-season-link" href="year.html?year=${season.year}">View tournament <span aria-hidden="true">→</span></a>
    </article>`;
  }).join("");
}

function renderHistoricalChampions() {
  document.querySelector("#historical-champions-grid").innerHTML = data.historical_seasons.map(season => {
    const lowScore = season.standings[0].net_total;
    const leaders = season.standings.filter(player => player.net_total === lowScore);
    return `<article class="champion-card historical-champion-card">
      <a class="champion-year" href="historical.html?year=${season.year}">${season.year}</a>
      <div class="champion-name"><span>Champion · partial record</span><strong>${leaders.map(player => player.name).join(" / ")}</strong></div>
      <div class="historical-card-summary"><span><small>Net total</small><strong>${lowScore}</strong></span><span><small>Recorded field</small><strong>${season.competitor_count}</strong></span></div>
      <a class="champion-season-link" href="historical.html?year=${season.year}">View leaderboard <span aria-hidden="true">→</span></a>
    </article>`;
  }).join("");
}

async function init() {
  try {
    const response = await fetch("data/sparta.json");
    if (!response.ok) throw new Error(`Data request failed (${response.status})`);
    data = await response.json();
    document.querySelector("#round-count").textContent = data.round_count;
    document.querySelector("#player-count").textContent = data.leaderboard.length;
    document.querySelector("#year-range").textContent = `${Math.min(...data.years)}–${Math.max(...data.years)}`;
    renderChampions();
    renderHistoricalChampions();
  } catch (error) {
    document.querySelector("main").innerHTML = `<section class="section shell"><div class="error">Could not load the Sparta archive: ${error.message}</div></section>`;
  }
}
init();
