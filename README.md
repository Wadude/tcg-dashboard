# TCG Collector's Desk

A private collector's dashboard for **Pokémon TCG** and **One Piece Card Game**: prices, meta, championships, releases, deals and demand for cards in my collection, in English, French and Japanese.

Dashboard: https://claude.ai/artifact/YGAafbEMp44rwbKs9RpV2q (private, claude.ai Dashboard type)

## Who it's for

- A collector (not mainly a player), living in Mauritius, on Réunion until 27 December 2026.
- Buys in physical shops for now: Sortilège, Popmarket, toy/kids shops and others.
- Prices in EUR first, with MUR alongside. Time zone UTC+4 (Réunion and Mauritius).
- Keep it as free as possible: free data sources only for now.

## Sections

- **Daily Hits**: a 2-minute morning read (around 7am UTC+4): deals, big movers, collection alerts, breaking news, today's events. "Quiet day" when nothing happened.
- **Weekly** (Monday): the full newsletter: championship results, what moved and why, collection demand report, market overview, what's coming. Archived.
- **Calendar**: set releases (JP / EN / FR) and championships.
- **My Collection**: cards owned, with demand signals (to be filled when the list arrives).
- **Shops**: local shops on Réunion and Mauritius.

## How the data works

Each dataset is a JSON file in `data/`, uploaded to the dashboard. A scheduled task refreshes them: daily for Daily Hits, weekly for the rest. The JSON files in this repo are the source of truth and keep the history.

| File | What it holds |
|---|---|
| `data/daily_hits.json` | Today's hits: one row per item |
| `data/weekly.json` | This week's newsletter: one row per section |
| `data/releases.json` | Upcoming and recent sets by region |
| `data/events.json` | Championships: recent results and upcoming |
| `data/movers.json` | Notable price moves |
| `data/meta.json` | Top decks / leaders and their share |
| `data/shops.json` | Local shops |
| `data/catalogue.json` | My card list (exported from my catalogue spreadsheet, without chat links) |
| `data/collection.json` | My cards with live prices, built by `scripts/build_collection.py` |
| `data/purchases.json` | What I've spent on packs, boxes and bundles (kept by hand) |

## Phases

1. Weekly newsletter + Daily Hits + summary dashboard from web research (now).
2. Daily price history saved to `data/`, a Deals page (free eBay developer API, account to be created by the owner), alerts.
3. Heat score, collection value over time, buy / hold / sell signals.

## Free sources

TCGdex (Pokémon cards EN/FR/JP), pokemontcg.io (EN prices incl. TCGplayer/Cardmarket), Limitless TCG (Pokémon and One Piece tournaments, English One Piece prices), Yuyu-tei (Japanese One Piece prices), official Pokémon and Bandai sites, web news. Japanese and One Piece prices are patchier.
