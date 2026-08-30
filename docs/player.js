const money = cents => `${cents < 0 ? "−" : ""}$${Math.abs(cents / 100).toFixed(2)}`;
const moneyClass = cents => cents > 0 ? "positive" : cents < 0 ? "negative" : "muted";
const ordinal = number => { const mod = number % 100; return `${number}${mod > 10 && mod < 14 ? "th" : ({1:"st",2:"nd",3:"rd"}[number % 10] || "th")}`; };

function scoreClass(score, par) {
  const relative = score - par;
  if (relative <= -2) return "eagle";
  if (relative === -1) return "birdie";
  if (relative === 1) return "bogey";
  if (relative >= 2) return "double-bogey";
  return "par";
}

function nineCells(values, start, formatter = value => value) {
  return values.slice(start, start + 9).map((value, offset) => `<td>${formatter(value, start + offset)}</td>`).join("");
}

function scorecard({round, player}) {
  const score = (value, index) => `<span class="score-mark ${scoreClass(value, round.pars[index])}">${value}</span>`;
  return `<article class="scorecard">
    <header><div><h3>${round.label}</h3><p>Handicap ${player.handicap} · Gross ${player.gross_total} · Net ${player.net_total}</p></div><strong class="${moneyClass(player.total_cents)}">${money(player.total_cents)}</strong></header>
    <div class="scorecard-scroll"><table class="golf-card">
      <thead><tr><th>Hole</th>${nineCells([1,2,3,4,5,6,7,8,9],0)}<th>Out</th>${nineCells([10,11,12,13,14,15,16,17,18],0)}<th>In</th><th>Total</th></tr></thead>
      <tbody>
        <tr class="par-row"><th>Par</th>${nineCells(round.pars,0)}<td>35</td>${nineCells(round.pars,9)}<td>35</td><td>70</td></tr>
        <tr><th>Gross</th>${nineCells(player.gross_scores,0,score)}<td>${player.gross_front}</td>${nineCells(player.gross_scores,9,score)}<td>${player.gross_back}</td><td>${player.gross_total}</td></tr>
        <tr class="net-row"><th>Net</th>${nineCells(player.net_scores,0)}<td>${player.net_front}</td>${nineCells(player.net_scores,9)}<td>${player.net_back}</td><td>${player.net_total}</td></tr>
      </tbody>
    </table></div>
    <footer><span>Holes ${money(player.holes.amount_cents)}</span><span>Front ${money(player.front_nine.amount_cents)}</span><span>Back ${money(player.back_nine.amount_cents)}</span><span>18 ${money(player.full_round.amount_cents)}</span></footer>
  </article>`;
}

async function init() {
  const requestedName = new URLSearchParams(location.search).get("name");
  try {
    const response = await fetch("data/sparta.json?v=6");
    if (!response.ok) throw new Error(`Data request failed (${response.status})`);
    const data = await response.json();
    const knownPlayer = data.leaderboard.find(player => player.name === requestedName);
    if (!requestedName || !knownPlayer) throw new Error("That golfer was not found in the archive.");

    const rounds = data.rounds.flatMap(round => {
      const player = round.players.find(item => item.canonical_name === requestedName);
      return player ? [{round, player}] : [];
    });
    const career = data.player_profiles[requestedName];
    document.title = `${requestedName} · Sparta International`;
    document.querySelector("#player-name").textContent = requestedName;
    document.querySelector("#player-subtitle").textContent = `${career.rounds} recorded rounds across ${career.season_count} seasons`;
    document.querySelector("#career-stats").innerHTML = [
      [money(career.total_cents), "Career winnings", moneyClass(career.total_cents)],
      [career.rounds, "Rounds played", ""],
      [career.average_net.toFixed(1), "Average net", ""],
      [career.best_net, "Best net", ""],
      [`${career.hole_wins}–${career.hole_losses}`, "Hole record", ""],
      [career.eagles, "Eagles or better", ""],
      [career.birdies, "Birdies", ""],
      [career.double_bogeys_or_worse, "Double bogeys or worse", ""],
      [career.best_gross, "Best gross round", ""],
      [career.worst_gross, "Worst gross round", ""],
      [career.first_place_finishes, "1st-place finishes", ""],
      [career.second_place_finishes, "2nd-place finishes", ""],
      [career.third_place_finishes, "3rd-place finishes", ""],
      [ordinal(career.best_finish), "Best finish", ""],
      [ordinal(career.worst_finish), "Worst finish", ""],
    ].map(([value,label,className]) => `<div class="stat-card"><strong class="${className}">${value}</strong><span>${label}</span></div>`).join("");

    document.querySelector("#season-grid").innerHTML = career.seasons.map(season => {
      return `<article class="season-card"><h3>${season.year}</h3><div class="season-row"><span>Finish</span><strong>${ordinal(season.finish)}</strong></div><div class="season-row"><span>Rounds</span><strong>${season.rounds}</strong></div><div class="season-row"><span>Average net</span><strong>${season.average_net.toFixed(1)}</strong></div><div class="season-row"><span>Hole record</span><strong>${season.hole_wins}–${season.hole_losses}</strong></div><div class="season-row"><span>Winnings</span><strong class="${moneyClass(season.total_cents)}">${money(season.total_cents)}</strong></div></article>`;
    }).join("");

    const sparta = career.sparta_handicap;
    document.querySelector("#sparta-handicap-panel").innerHTML = sparta.available
      ? `<div class="sparta-handicap-panel">
          <div class="sparta-handicap-index"><strong>${sparta.playing_handicap}</strong><span>${sparta.current ? `${sparta.target_year} playing handicap` : "Last calculated handicap"}</span></div>
          <div class="sparta-handicap-breakdown">
            <div class="sparta-handicap-heading"><strong>Based on ${sparta.source_year}</strong><span class="${sparta.current ? "current" : "stale"}">${sparta.current ? "Current" : `Outside ${sparta.lookback_years}-year window`}</span></div>
            <div class="sparta-round-values">${sparta.rounds.map(round => `<div><span>Day ${round.day}</span><strong>${round.gross_total}</strong><small>(${round.gross_total} − 70) × .875 = ${round.round_handicap.toFixed(1)}</small></div>`).join("")}</div>
            <p>Three-round average: <strong>${sparta.value.toFixed(1)}</strong> · Playing handicap: <strong>${sparta.playing_handicap}</strong></p>
          </div>
          <p class="sparta-handicap-rule">The following season uses the average of all three round values. During the tournament, each next-day handicap is the average of the current handicap and the previous round's value.</p>
        </div>`
      : `<div class="handicap-unavailable"><strong>No Sparta handicap available</strong><p>A complete three-round season is required.</p></div>`;

    const roundYears = career.seasons.map(season => season.year);
    const yearFilter = document.querySelector("#round-year-filter");
    yearFilter.innerHTML = roundYears.map(year => `<option value="${year}">${year}</option>`).join("");
    const renderRoundYear = () => {
      const year = Number(yearFilter.value);
      const yearRounds = rounds
        .filter(item => item.round.year === year)
        .sort((a,b) => a.round.day-b.round.day);
      document.querySelector("#player-rounds").innerHTML = `<div class="year-scorecards">${yearRounds.map(scorecard).join("")}</div>`;
    };
    yearFilter.addEventListener("change", renderRoundYear);
    renderRoundYear();
  } catch (error) {
    document.querySelector("#player-name").textContent = "Profile unavailable";
    document.querySelector("#profile-content").innerHTML = `<section class="section shell"><div class="error">${error.message}</div></section>`;
  }
}
init();
