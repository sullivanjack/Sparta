# Sparta International

Sparta is a golf gambling game in which everyone plays everyone. This repository contains the official historical scorecards, a settlement calculator, and a static archive for GitHub Pages.

## The game

All bets use handicap-adjusted (net) scores. Each player is compared head-to-head with every other player in the field:

| Bet | Stake per opponent |
| --- | ---: |
| Each hole | $0.10 |
| Front nine total | $0.50 |
| Back nine total | $0.50 |
| Full 18 total | $1.00 |

Lower score wins. An aggregate-score tie is a push: neither player wins or loses that bet.

Sparta has one distinctive hole rule: when players tie a hole, their score on the next hole breaks the tie. If that is also tied, comparison continues forward through hole 18. A tie still unresolved at hole 18 is a push. The comparison does not wrap from hole 18 back to hole 1.

Every settlement is zero-sum. The money won across the field must exactly equal the money lost.

### Handicap strokes

The first scorecard row provides the difficulty rank of each hole, from 1 (hardest) through 18 (easiest). Handicap strokes are allocated in that order. For example, a 20-handicap player receives one stroke on every hole and a second stroke on handicap holes 1 and 2.

The event uses a nine-hole, par-35 course played twice from different tees. Hole pars are `4, 4, 4, 5, 3, 3, 4, 4, 4` on both nines, for a par of 70.

Golfer profiles also include an estimated World Handicap System index derived from historical Sparta rounds. The estimate uses a Course Rating of 67.6, Slope Rating of 112, PCC 0, net-double-bogey adjusted gross scores, and the WHS fewer-than-20-scores table. It cannot reproduce caps, exceptional-score reductions, or committee adjustments that are not present in the archive.

## Calculate a round

Python 3.10 or newer is recommended. The calculator has no third-party dependencies.

```bash
python3 Sparta.py data/rounds/2025/Sparta2025_Day1.csv
```

This writes `data/rounds/2025/Sparta2025_Day1_Output.csv`, replacing an existing report rather than appending to it. JSON is also available:

```bash
python3 Sparta.py data/rounds/2025/Sparta2025_Day1.csv --format json --output day1.json
```

The older `--inputFile` argument remains accepted for compatibility.

### Input format

```csv
Name,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,Handicap
Handicap,16,18,6,10,12,8,2,4,14,15,17,3,9,11,7,1,5,13,-1
Player Name,5,4,6,7,4,5,5,4,4,5,6,5,7,3,4,5,5,4,18
```

The importer validates the header, all 18 scores, unique player names, non-negative handicaps, and a complete 1–18 hole-rank permutation. It also understands the known vertical handicap-row export in the 2023 archive and the `+AC0-1` encoding artifact in 2025.

## Build the historical site data

The static site lives in `docs/` and reads one generated JSON file. Its homepage links to a dedicated overview for every archived year, with season leaderboards and day-by-day results; golfer names link to individual career profiles and golf-style scorecards.

```bash
python3 scripts/build_site_data.py
```

The command discovers source scorecards under `data/rounds/<year>/`, validates and settles every round, then writes `docs/data/sparta.json`. Python precomputes all season standings, money rankings, player profiles, finish counts, scoring statistics, and round placements; the browser only renders those results. The command exits unsuccessfully if any input cannot be processed, so bad scorecards cannot silently enter the archive.

To preview the site locally:

```bash
python3 -m http.server 8000 --directory docs
```

Open `http://localhost:8000`. To publish, configure GitHub Pages to deploy from the `docs` directory on the default branch.

### Player aliases

Historical spelling changes are normalized for all-time statistics in `scripts/build_site_data.py`. Aliases currently join `Ralph` with `Ralph Reis`, `Leo` with `Leo Berhost`, and `Tim Stefl` with `Tim Steffl`. Original names remain visible on individual scorecards.

## Test

```bash
PYTHONPYCACHEPREFIX=/tmp/sparta-pycache python3 -m unittest discover -s tests -v
```

The tests cover handicap allocation, tie-breaking, zero-sum settlement, and every historical source scorecard.

## Project layout

```text
Sparta.py                  CLI entry point
sparta/game.py             Pure scoring and settlement rules
sparta/io.py               Validated historical CSV importer
sparta/report.py           CSV and JSON report writers
scripts/build_site_data.py Historical data generator
tests/                     Calculator and archive tests
docs/                      GitHub Pages site
data/rounds/2019/ … 2025/  Original scorecards and legacy reports
data/archive/               Older spreadsheets and saved experiments
```
