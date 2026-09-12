const playerLink = name => `player.html?name=${encodeURIComponent(name)}`;

function lastName(name) {
  const parts = name.trim().split(/\s+/);
  return `${parts.at(-1)} ${parts.slice(0, -1).join(" ")}`;
}

async function init() {
  const directory = document.querySelector("#player-directory");
  const meta = document.querySelector("#player-directory-meta");
  const search = document.querySelector("#player-search");

  try {
    const response = await fetch("data/sparta.json?v=8", {cache: "no-store"});
    if (!response.ok) throw new Error(`Data request failed (${response.status})`);
    const data = await response.json();
    const players = [...data.leaderboard].sort((left, right) =>
      lastName(left.name).localeCompare(lastName(right.name))
    );

    const render = () => {
      const query = search.value.trim().toLocaleLowerCase();
      const matches = players.filter(player => player.name.toLocaleLowerCase().includes(query));
      meta.textContent = `${matches.length} ${matches.length === 1 ? "golfer" : "golfers"}`;
      directory.innerHTML = matches.length
        ? matches.map(player => `<a class="player-directory-card" href="${playerLink(player.name)}">
            <div><strong>${player.name}</strong><small>${player.rounds} recorded rounds · ${player.years.length} ${player.years.length === 1 ? "season" : "seasons"}</small></div>
            <span aria-hidden="true">→</span>
          </a>`).join("")
        : `<div class="player-directory-empty">No golfers found.</div>`;
    };

    search.addEventListener("input", render);
    render();
  } catch (error) {
    meta.textContent = "";
    directory.innerHTML = `<div class="error">Could not load the player directory: ${error.message}</div>`;
  }
}

init();
