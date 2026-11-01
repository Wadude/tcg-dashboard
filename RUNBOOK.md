# Update runbook

How the scheduled runs refresh the TCG Collector's Desk. Each run starts fresh: read this file, then `README.md` for who the collector is.

- Project: `D:\CLAUDE\tcg-dashboard` on the PC, https://github.com/Wadude/tcg-dashboard (private) in the cloud. Start by pulling `main`.
- Dashboard: https://claude.ai/artifact/YGAafbEMp44rwbKs9RpV2q (claude.ai Dashboard type; its content lives in its store, written with the `ArtifactData` tool, data files uploaded with the `Artifact` tool)
- The JSON files in `data/` are the source of truth. Edit them, then upload. Never invent prices, dates or results: every fact needs a source URL, and anything unconfirmed says so.
- Write in plain, short English for a collector (not a player). Prices in EUR with MUR alongside (rate in `scripts/build_collection.py`, `RATE`; refresh it weekly from valutafx.com/eur-mur.htm).

## Data files and their rows

| Dataset id | File | Row fields |
|---|---|---|
| `daily_hits` | `data/daily_hits.json` | id, date ("Mon 2 Nov 2026" on every row), kind (deal / mover / collection / news / event), game (Pokémon / One Piece / Both), importance (High / Medium / ""), title, detail, source, url |
| `weekly` | `data/weekly.json` | id, edition (same on every row), order, game, heading, body (paragraphs split by a blank line), source, url |
| `releases` | `data/releases.json` | id, game, region, name, date (ISO, for sorting), when (display), details, status (Released / Pre-order / Upcoming), url |
| `events` | `data/events.json` | id, game, name, date (ISO), when, location, status (Done / Upcoming), result, url |
| `movers` | `data/movers.json` | id, game, item, language, change ("+12%" / "−9%"), price (display text), why, url |
| `meta` | `data/meta.json` | id, game, deck, share (0–1), key_cards |
| `shops` | `data/shops.json` | id, name, island (Réunion / Mauritius / Online), town, games, notes, url, url_label |
| `collection` | `data/collection.json` | built by `scripts/build_collection.py`; don't hand-edit prices |

A file must never be an empty list (the dashboard can't read it). For a quiet day, `daily_hits` keeps one row: kind "news", title "Quiet day", detail saying nothing new since yesterday.

## Good sources

- Pokémon: pokemon.com and press.pokemon.com, pokebip.com (French), serebii.net, limitlesstcg.com (results, upcoming events, decks), TCGdex API `https://api.tcgdex.net/v2/{fr|en|ja}/cards/{setId}-{number}` (Cardmarket prices: `pricing.cardmarket.trend`, `avg7`, `avg30`).
- One Piece: en.onepiece-cardgame.com and onepiece-cardgame.com (products, ban list), onepiece.limitlesstcg.com (results, upcoming, card prices), opboxindex.com (box prices), play-in.com (French products).
- Réunion shops: sortileges.re, miyatakardmarket.re (shows stock), planetgeek.re, punkrecords-tcg.com, mirageisland974.re.
- Cardmarket, PokeBeach and PriceCharting block automated reading; use the sources above.

## Publishing a change

1. Edit the JSON file(s) and check each parses (`node -e "JSON.parse(require('fs').readFileSync('data/x.json','utf8'))"`).
2. Upload each changed file: `Artifact` publish with `url` = the dashboard, `asset: true`, `file_path` = the file. Note the returned `/_blob/<id>`.
3. `ArtifactData` `get` collection `datasets`, doc_id = the dataset id, to learn its `version` and old `source.url`.
4. `ArtifactData` `batch` of `update`s (each with `if_version`): `source: {kind: "file", url: "/_blob/<new id>", name: "<file>.json"}` and `updated: {at: <ISO now>, by: "Claude (scheduled)"}`.
5. Delete the previous blob: `Artifact` `delete` with `url` and `path` = the old blob id (only after the update succeeded).
6. Don't change `files/index.html` (the page) in a scheduled run. Page changes are done with the collector in a normal session.
7. `git add -A` and commit ("Daily Hits 2 Nov 2026" / "Weekly edition, week of 2 Nov 2026"), ending the message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, then push to `main` on https://github.com/Wadude/tcg-dashboard (private) so the next run, local or cloud, starts from today's data. Pull first if the push is refused.

## Daily run (every morning)

Goal: a 2-minute read of what is new since yesterday's `daily_hits`. Usually 3–8 items; fewer is fine.

1. Read yesterday's `data/daily_hits.json` so nothing repeats.
2. Search for: Pokémon and One Piece news in the last 24–48 hours (reveals, reprints, ban lists, pre-orders opening, release-day news, especially French products); results of events in `data/events.json` that finished since yesterday; events happening today or this weekend; new stock or pre-orders on the Réunion shops' websites (until 27 Dec 2026).
3. Price checks (keep it light): for the 15 most valuable cards in `data/collection.json` with a TCGdex id, and the chase cards named in `data/movers.json`, compare `avg7` with `avg30`; a move of 20% or more is a "mover" hit (or a "collection" hit when the collector owns the card). Deals: a card the collector would want that is trading clearly below its 30-day average.
4. Write the new `data/daily_hits.json` (today's date on every row) and update `releases` / `events` status if something was released or finished (set the result).
5. Publish the changed files and commit.

## Weekly run (Monday)

Do the daily run's steps first if it hasn't run today, then:

1. Archive last week's edition: copy `data/weekly.json` to `data/archive/weekly-<edition date>.json`.
2. Refresh the collection: `python scripts/build_collection.py` (reads the card list in `data/catalogue.json`, writes `data/collection.json`; standard library only). When the collector adds or changes cards, update `data/catalogue.json` (same fields) in a normal session.
3. Research the week (in parallel subagents if available): Pokémon (releases EN/FR/JP for the next 4 months, last week's results, upcoming events, meta shares from Limitless, price movers via TCGdex), One Piece (same, with Limitless and opboxindex), and the Réunion/Mauritius shops.
4. Rewrite `releases`, `events` (drop events finished more than 6 weeks ago), `movers` (10–15 rows, the biggest moves), `meta`.
5. Write the new `data/weekly.json`, edition "Week of <Monday's date>". Sections, in order: The week in short; one section per big story (2–5); Championships; Your collection (what moved among the collector's cards, what to hold or sell, using the demand signals); Language gaps; Réunion window (days left until 27 Dec; after that, buying from Mauritius); Coming up; About the numbers. Compare with last week's archive where useful.
6. Publish every changed file and commit.
