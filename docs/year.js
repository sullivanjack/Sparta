const money = cents => `${cents < 0 ? "−" : ""}$${Math.abs(cents / 100).toFixed(2)}`;
const moneyClass = cents => cents > 0 ? "positive" : cents < 0 ? "negative" : "muted";
const playerLink = name => `player.html?name=${encodeURIComponent(name)}`;

function dayTable(round) {
  return `<div class="day-results table-card dark-card"><table><thead><tr><th>Place</th><th>Player</th><th>HCP</th><th>Gross</th><th>Net</th><th>Holes</th><th>Front</th><th>Back</th><th>18</th><th class="money">Total</th></tr></thead><tbody>${round.players.map(p => `<tr><td class="muted">${p.net_rank}</td><td><a class="player-link light-link" href="${playerLink(p.canonical_name)}"><strong>${p.name}</strong></a></td><td>${p.handicap}</td><td>${p.gross_total}</td><td><strong>${p.net_total}</strong></td><td class="${moneyClass(p.holes.amount_cents)}">${money(p.holes.amount_cents)}</td><td class="${moneyClass(p.front_nine.amount_cents)}">${money(p.front_nine.amount_cents)}</td><td class="${moneyClass(p.back_nine.amount_cents)}">${money(p.back_nine.amount_cents)}</td><td class="${moneyClass(p.full_round.amount_cents)}">${money(p.full_round.amount_cents)}</td><td class="money ${moneyClass(p.total_cents)}">${money(p.total_cents)}</td></tr>`).join("")}</tbody></table></div>`;
}

async function init() {
  const requestedYear = Number(new URLSearchParams(location.search).get("year"));
  try {
    const response = await fetch("data/sparta.json");
    if (!response.ok) throw new Error(`Data request failed (${response.status})`);
    const data = await response.json();
    const rounds = data.rounds.filter(round => round.year === requestedYear).sort((a,b) => a.day-b.day);
    if (!rounds.length) throw new Error("That year was not found in the archive.");
    const season = data.seasons.find(season => season.year === requestedYear);
    const players = season.standings;
    document.title = `${requestedYear} · Sparta International`;
    document.querySelector("#season-title").textContent = requestedYear;
    document.querySelector("#season-subtitle").textContent = `${season.round_count} days · ${season.competitor_count} competitors · ${season.scorecard_count} recorded scorecards`;
    document.querySelector("#year-leaderboard-head").innerHTML = `<th>Rank</th><th>Player</th>${rounds.map(round => `<th>Day ${round.day} net</th><th>Day ${round.day} HCP</th>`).join("")}<th>Total</th><th class="money">Winnings</th>`;
    document.querySelector("#year-leaderboard").innerHTML = players.map(p => `<tr><td class="muted">${p.rank}</td><td><a class="player-link" href="${playerLink(p.name)}"><strong>${p.name}</strong></a></td>${rounds.map(round => `<td>${p.day_scores[round.day] ?? "—"}</td><td class="muted">${p.day_handicaps[round.day] ?? "—"}</td>`).join("")}<td><strong>${p.total_net}</strong></td><td class="money ${moneyClass(p.total_cents)}">${money(p.total_cents)}</td></tr>`).join("");
    const dayFilter = document.querySelector("#day-filter");
    dayFilter.innerHTML = rounds.map(round => `<option value="${round.day}">Day ${round.day}</option>`).join("");
    const renderDay = () => {
      const round = rounds.find(item => item.day === Number(dayFilter.value));
      document.querySelector("#day-result").innerHTML = dayTable(round);
    };
    dayFilter.addEventListener("change", renderDay);
    renderDay();
  } catch (error) {
    document.querySelector("#season-title").textContent = "Season unavailable";
    document.querySelector("#year-content").innerHTML = `<section class="section shell"><div class="error">${error.message}</div></section>`;
  }
}
init();
