const money = cents => `${cents < 0 ? "−" : ""}$${Math.abs(cents / 100).toFixed(2)}`;
const moneyClass = cents => cents > 0 ? "positive" : cents < 0 ? "negative" : "muted";
const ordinal = number => { const mod = number % 100; return `${number}${mod > 10 && mod < 14 ? "th" : ({1:"st",2:"nd",3:"rd"}[number % 10] || "th")}`; };
const playerLink = name => `player.html?name=${encodeURIComponent(name)}`;
let data;

function statsForYear(year) {
  if (year === "all") return data.leaderboard;
  return data.seasons.find(season => String(season.year) === year).money_standings;
}

function renderLeaderboard() {
  const players = statsForYear(document.querySelector("#year-filter").value);
  document.querySelector("#podium").innerHTML = players.slice(0,3).map((p,index) => `<a class="podium-card" href="${playerLink(p.name)}"><span class="podium-rank">${index+1}</span><div><h3>${p.name}</h3><p>${money(p.total_cents)} · ${p.rounds} rounds</p></div></a>`).join("");
  document.querySelector("#leaderboard-body").innerHTML = players.map((p,index) => `<tr><td class="muted">${ordinal(index+1)}</td><td><a class="player-link" href="${playerLink(p.name)}"><strong>${p.name}</strong></a></td><td>${p.rounds}</td><td>${p.average_gross.toFixed(1)}</td><td>${p.hole_wins}–${p.hole_losses}</td><td class="money ${moneyClass(p.total_cents)}">${money(p.total_cents)}</td></tr>`).join("");
}

function renderYears() {
  document.querySelector("#year-cards").innerHTML = data.seasons.map(season => {
    return `<a class="year-card" href="year.html?year=${season.year}"><span class="year-number">${season.year}</span><div><strong>${season.round_count} days</strong><span>${season.competitor_count} competitors</span></div><i aria-hidden="true">→</i></a>`;
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
    document.querySelector("#year-filter").insertAdjacentHTML("beforeend", data.years.map(year => `<option value="${year}">${year}</option>`).join(""));
    document.querySelector("#year-filter").addEventListener("change", renderLeaderboard);
    renderLeaderboard(); renderYears();
  } catch (error) {
    document.querySelector("main").innerHTML = `<section class="section shell"><div class="error">Could not load the Sparta archive: ${error.message}</div></section>`;
  }
}
init();
