# 2026 scorecard templates

These files are kept in `templates/` so incomplete scorecards are not included in the site build.

- Day 1 handicaps come from the final workbook's `2026 Hdcp` column and are rounded to the nearest whole stroke.
- Bob Breslin and Greg Nestor use their complete 2024 seasons through the two-year fallback.
- Jon Moreau and Sam Sullivan are new and need starting handicaps.
- Day 2 and Day 3 handicaps should be entered after the prior day's Sparta adjustment is calculated.

Populate a card's handicap column with the shared calculator:

```bash
python3 scripts/calculate_sparta_handicaps.py data/rounds/2026/templates/Sparta2026_Day1.csv --year 2026 --day 1
```

For Day 2 or Day 3, first put the completed earlier scorecard(s) in `data/rounds/2026/`, then run the same command with the target template and day number. The calculator retains the unrounded value between days and writes the nearest whole-stroke playing handicap to the CSV.

After all 18 scores and the handicap are filled in, move the completed card to the parent `data/rounds/2026/` directory. Keep the filename `Sparta2026_Day1.csv`, `Sparta2026_Day2.csv`, or `Sparta2026_Day3.csv` so the site builder can discover it.

Names were matched to the existing archive. In particular, use `Edwin Erhlbacher`, `Ralph Reis`, `Leo Berhost`, `Matt Lawrence`, `Jeremy Flynn`, `Tim Steffl`, and `Joe McCardell`.
