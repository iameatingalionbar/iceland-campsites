# Iceland Campsites for Campervans: project notes

Static English info site. Plain HTML + one CSS file, built by a Python 3 stdlib script (no dependencies).
Hard rules: **no invented prices, hours or facilities.** Every fact has a source URL and a check date.
Anything not confirmed is rendered as a visible **Unconfirmed** badge. Vague source wording ("depending on weather",
"upon request") or conflicting sources → winter status `call-ahead` (or `partial`), never `open`.

## Build & preview

```bash
cd /workspace/iceland-campsites
python3 build.py                       # data/ + templates/ + static/ -> dist/  (fails on any unsourced fact)
BASE_URL=https://your-domain.is python3 build.py   # canonical URLs, sitemap, robots use this
python3 check.py                       # internal links/anchors, tag balance, <title>/description/canonical/viewport, sitemap
python3 -m http.server -d dist 8000    # preview at http://localhost:8000/
python3 make_preview.py                # standalone guide with CSS inlined -> south-coast-winter-preview.html
/tmp/pwvenv/bin/python screenshot.py   # full-page PNG -> screenshots/south-coast-winter.png
#   (venv: python3 -m venv /tmp/pwvenv && /tmp/pwvenv/bin/pip install playwright; uses /usr/bin/google-chrome)
```

Exit codes: `build.py` and `check.py` exit non-zero on failure. A nightly run should be:
`python3 build.py && python3 check.py && python3 make_preview.py`.

## Layout

```
data/site.json               site name, base_url, regions (8), themes (2)
data/campsites/<slug>.json   one file per campsite -> dist/campsites/<slug>/index.html
data/guides/<slug>.json      editorial guides       -> dist/guides/<slug>/index.html
templates/base.html          page shell (string.Template: $title $description $canonical $body $root ...)
static/style.css             the only stylesheet
build.py, check.py, make_preview.py, screenshot.py
scripts/seed_south_coast_2026-10-23.py   one-off generator used for the 13 South Coast entries (kept for provenance)
dist/                        build output (git-ignored)
```

Generated pages: home, /campsites/ (all), /campsites/<slug>/, /regions/ + 8 region hubs, /themes/ + 2 theme hubs
(open-in-winter, dump-stations), /guides/ + guides, /about/ (sources & methodology), /affiliate-disclosure/, 404.html,
sitemap.xml, robots.txt. Region and theme hubs fill in automatically from the campsite data.

## Data schema (campsite)

A **fact** is `{"value": string|null, "src": [source keys], "note"?: string}`.
- `value: null` → page shows **Unconfirmed** + `note`.
- A non-null `value` with an empty or missing `src` → **build fails**. An unknown source key → build fails.

```jsonc
{
  "slug": "kebab-case", "name": "...", "alt_names": ["..."], "region": "south",   // a region slug from site.json
  "town": "...", "completeness": "full|stub", "checked": "YYYY-MM-DD",
  "sources": { "<key>": {"title": "...", "url": "https://...", "checked": "YYYY-MM-DD"} },
  "intro": FACT,                                   // optional, sourced
  "location": {"address": FACT, "lat": num|null, "lon": num|null, "coords_src": [keys]},
  "season": FACT,
  "winter": {"status": "open|partial|call-ahead|closed|unconfirmed", "value": str, "src": [keys]},
  "prices": {"applies_to": FACT /* e.g. '2026 rates' */, "currency": "ISK",
             "items": [ {"label": "Adult per night", "value": "2,500 ISK"|null, "src": [...], "note"?: ...} ]},
  "facts": { "electricity": FACT, "kitchen": FACT, "showers": FACT, "toilets": FACT,
             "dump_station": FACT + {"has": "yes|no|nearby|null"}, "wifi": FACT, "laundry": FACT,
             "camping_card": FACT, "contact": FACT },
  "practical": [FACT, ...]                         // sourced tips only
}
```
Theme filters: `open-in-winter` lists `winter.status` ∈ {open, call-ahead, partial}. `dump-stations` lists `dump_station.has == "yes"` by region, plus `nearby`.
Guide schema: `slug, title, description, region, checked, sources{}, intro[FACT], scope_note, demand FACT, campsites[slugs], tips[FACT]`.
Guide tables pull each campsite's winter/electricity/dump/adult price straight from the campsite files, so update the campsite file, not the guide.

Status rules: `open` = an official or own source says it is open through winter, with no conflicting source. `call-ahead` = listed as winter-open but the wording is vague or sources conflict. `partial` = shoulder season (e.g. to Nov/Dec, or from March). `closed` = published season ends before winter.

Useful source: tjalda.is is a JS app, but `https://tjalda.is/api/campsites` returns public JSON for about 181 campsites (name, slug, address, GPS, opening_time flag '1'/'2', season text, prices_en, services). Cite the human page `https://tjalda.is/en/campsite/<slug>`.
Treat it as a lead, not gospel: its "Open all year" service tag sometimes conflicts with its own season text (e.g. Hvolsvöllur).

## Backlog (prioritised; machine-readable)

Columns: `id | prio (1 = highest) | status (todo|stub|done) | type | slug | title | region | why | seed sources`.
A nightly run should take the first `todo` (or `stub` → full) row by prio, research it, write `data/...json`, set the status, and log it in the CHANGELOG.

| id | prio | status | type | slug | title | region | why | seed sources |
|---|---|---|---|---|---|---|---|---|
| B01 | 1 | done | guide | south-coast-winter-campsites | Campsites Open in Winter on Iceland's South Coast (2026–27) | south | top winter question (Reddit) | ferdalag winter list, tjalda |
| B02 | 1 | done | campsite | reykjavik-eco-campsite | Reykjavík Eco-Campsite | capital-area | flagship, open all year | reykjavikcampsite.is |
| B03 | 1 | stub | campsite | skaftafell | Skaftafell Campground (full page) | south | only winter site Vík–Höfn | vatnajokulsthjodgardur.is |
| B04 | 1 | stub | campsite | selfoss-gesthus | Selfoss Gesthús (full page) | south | open all year, kitchen | gesthus.is |
| B05 | 1 | stub | campsite | hellisholar | Hellishólar (full page; dump?) | south | winter area G | hellisholar.is |
| B06 | 1 | todo | guide | dump-stations-iceland | Where to empty a cassette toilet in Iceland (by region) | all | dump-station theme hub needs data | uos.is disposal list, icetourist.is |
| B07 | 1 | todo | campsite | sandgerdi-airport-camping | Sandgerði / airport-area campsite | reykjanes | first/last night near KEF, all year | tjalda |
| B08 | 1 | todo | campsite | hamrar-akureyri | Hamrar, Akureyri | north-east | all year | tjalda, hamrar.is |
| B09 | 1 | todo | campsite | vogar-myvatn | Vogar, Mývatn | north-east | all year, chemical disposal | tjalda, vogarholidays.is |
| B10 | 1 | todo | campsite | camp-egilsstadir | Camp Egilsstaðir | east | all year 24/7 | tjalda |
| B11 | 2 | todo | guide | golden-circle-winter-campsites | Winter campsites on the Golden Circle (2026–27) | south | Úthlíð/Skjól/Geysir/Laugarvatn/Flúðir conflicts to resolve | ferdalag winter list |
| B12 | 2 | todo | campsite | uthlid | Úthlíð | south | winter service list | tjalda, ferdalag |
| B13 | 2 | todo | campsite | skjol | Skjól (Geysir area) | south | conflict: year-round vs card dates 21 May–15 Sep | tjalda, utilegukortid |
| B14 | 2 | todo | campsite | thingvellir-leirar | Þingvellir – Leirar | south | national park, winter? | thingvellir.is |
| B15 | 2 | todo | campsite | hotel-laugarvatn-camping | Laugarvatn | south | winter service list | ferdalag |
| B16 | 2 | todo | campsite | fludir | Flúðir | south | winter service list | ferdalag, tjalda |
| B17 | 2 | todo | campsite | hverinn-kleppjarnsreykir | Hverinn, Kleppjárnsreykir | west | hot spring site | tjalda |
| B18 | 2 | todo | campsite | stykkisholmur | Stykkishólmur | west | Snæfellsnes base | tjalda |
| B19 | 2 | todo | campsite | grundarfjordur | Grundarfjörður | west | Kirkjufell | tjalda |
| B20 | 2 | todo | campsite | mosskogar | Mosskógar (Mosfellsdalur) | capital-area | 2nd capital option | tjalda |
| B21 | 2 | todo | campsite | gardskagi | Garðskagi | reykjanes | lighthouse, near KEF | tjalda |
| B22 | 2 | todo | campsite | grindavik | Grindavík | reykjanes | check post-eruption status | tjalda, grindavik.is |
| B23 | 2 | todo | campsite | djupivogur | Djúpivogur | east | Ring Road east | tjalda |
| B24 | 2 | todo | campsite | seydisfjordur | Seyðisfjörður | east | ferry port | tjalda |
| B25 | 3 | todo | campsite | holmavik | Hólmavík | westfjords | Westfjords entry | tjalda |
| B26 | 3 | todo | campsite | thingeyri | Þingeyri | westfjords | Westfjords | tjalda |
| B27 | 3 | todo | campsite | isafjordur-tungudalur | Ísafjörður – Tungudalur | westfjords | main town | tjalda |
| B28 | 3 | todo | campsite | blonduos | Blönduós | north-west | Ring Road | tjalda |
| B29 | 3 | todo | campsite | myllulaekur | Myllulækur (Nesjar) | south | to late Oct, weather permitting | tjalda |
| B30 | 3 | todo | campsite | vestrahorn-stokksnes | Vestrahorn / Stokksnes camping | south | photo spot | tjalda |
| B31 | 3 | todo | guide | camping-card-2026 | Is the Camping Card (Útilegukortið) worth it in 2026? | all | demand | utilegukortid.is |
| B32 | 3 | todo | task | south-coast-stubs-dump | Confirm dump/electricity for Starlight, Farmhouse Lodge, Smáratún, Hellishólar, Kirkjubær | south | Unconfirmed cells in guide B01 | email/phone needs Stefán's OK |

Done South Coast stubs (status `stub`, individual pages exist): hveragerdi-reykjamork, hella-arhus, hvolsvollur, smaratun-fljotshlid,
starlight-lambafell, skogafoss, farmhouse-lodge-skeidflot, vik-camping, kirkjubaer-ii, hofn.

## Competitor & demand notes
- mapoficeland.is: competitor, **reference only, never copy text or data.**
- Reddit r/VisitingIceland: demand evidence only (fetch is blocked, so cite threads found via search results), e.g.
  https://www.reddit.com/r/VisitingIceland/comments/193fqbr/winter_campground_in_vik/ and
  https://www.reddit.com/r/VisitingIceland/comments/1gytpl5/campsite_recommendations/

## Monetization (awaiting Stefán)
Nothing signed up, no links placed. The affiliate disclosure page is a placeholder. Options to review:
| program | url | stated terms (from their page, not verified further) |
|---|---|---|
| Go Campers | https://www.gocampers.is/partner-with-us/ | 5% commission, ~$120 average commission per booking, 5-month cookie |
| Campervan Iceland | https://www.campervaniceland.com/affiliate-program | terms not reviewed yet |
| Camper Rental Iceland | https://www.camperrentaliceland.com/affiliates | terms not reviewed yet |

## Decisions for Stefán (nothing bought)
- Domain ideas (availability not checked): icelandcampsites.is, campervancampsites.is, wintercamping.is, campiceland.info.
  .is costs ISK 8,220/year incl. VAT (ISNIC, https://www.isnic.is/en/payments?tab=isk, checked 2026-10-23).
- Hosting (all static, free tiers): Cloudflare Pages Free (unlimited static bandwidth, 500 builds/mo; https://developers.cloudflare.com/pages/platform/limits/),
  Netlify Free ($0, 300 credits/mo hard limit; https://www.netlify.com/pricing), or GitHub Pages (free for public repos).
- Contacting campsites to fill Unconfirmed cells (email/phone) needs your approval.

## CHANGELOG
- 2026-10-23: Project created. Stdlib build (`build.py`), checker (`check.py`), base template, CSS, 8 regions, 2 themes,
  About/methodology, affiliate-disclosure placeholder, sitemap/robots.
- 2026-10-23: Reykjavík Eco-Campsite full page (2026 prices, winter Area A rules, Klettagarðar 14 dump point).
- 2026-10-23: First guide: "Campsites Open in Winter on Iceland's South Coast (2026–27)" plus 13 South Coast campsite
  entries (12 stubs + Skaftafell/Selfoss/Hellishólar data). Screenshot + standalone preview generated.
