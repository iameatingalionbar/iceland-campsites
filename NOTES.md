# Iceland Campsites for Campervans: project notes

Static English info site. Plain HTML + one CSS file, built by a Python 3 stdlib script (no dependencies).
Hard rules: **no invented prices, hours or facilities.** Every fact has a source URL and a check date.
Anything not confirmed is rendered as a visible **Unconfirmed** badge. Vague source wording ("depending on weather",
"upon request") or conflicting sources → winter status `call-ahead` (or `partial`), never `open`.

## Deploy (GitHub Pages, custom domain) — every nightly run MUST finish with `./deploy.sh`

Live site: **https://icelandcampsites.com/** (GitHub Pages, repo iameatingalionbar/iceland-campsites, public, gh-pages `/`).
https://www.icelandcampsites.com/ and the old https://iameatingalionbar.github.io/iceland-campsites/... 301-redirect to the apex
(path preserved). HTTPS enforced (Let's Encrypt cert issued by GitHub for apex + www, auto-renewed).
`./deploy.sh` = build with BASE_URL=https://icelandcampsites.com (no path prefix) → `check.py` → `serve_check.py`
(aborts on any problem) → verify dist/CNAME → commit + push source to `main` → force-push `dist/` (+ `.nojekyll`, `CNAME`) to `gh-pages` →
ensure Pages source = gh-pages `/` + cname icelandcampsites.com via REST (GET /pages, then PUT, or POST if missing) → request a
Pages build → if `https_enforced` is false, PUT it true (non-fatal; GitHub refuses until the cert exists).
**dist/CNAME must stay**: build.py writes it from the BASE_URL host (skipped for *.github.io/localhost builds); without it a deploy
drops the custom domain. All internal links are relative (`$root`), 404.html uses root-absolute `/...` links, so the site works at
the domain root or under a prefix; check.py fails on a missing/wrong CNAME, stale github.io/example.com URLs or a hard-coded
`/iceland-campsites` prefix.

### Domain & DNS (icelandcampsites.com, bought by Stefán at Cloudflare 2026-10-27)
Cloudflare DNS (nameservers bruce/kami.ns.cloudflare.com), all records **DNS only** (grey cloud — proxying would break GitHub's cert):
`A @ 185.199.108.153 / 185.199.109.153 / 185.199.110.153 / 185.199.111.153`, `CNAME www iameatingalionbar.github.io`.
Check: `dig +short icelandcampsites.com @1.1.1.1` (dig is not installed on the box; use DoH:
`curl -s -H 'accept: application/dns-json' 'https://1.1.1.1/dns-query?name=icelandcampsites.com&type=A'`).
Domain renewal is at Cloudflare (Stefán's account). Note: the box's egress proxy answers plain http:// with 500, so http→https
redirects cannot be tested from the box.
Auth: env var `GITHUB_TOKEN_CAMPSITES` (fine-grained; Contents/Pages/Administration write on this repo only), read by the
repo-local git credential.helper and sent to the API via a stdin header. Never print it or write it to a file or git config.
HTTPS only (SSH is blocked from the box). Non-zero exit = deploy failed; report the HTTP status/message.

## Build & preview

```bash
cd /workspace/iceland-campsites
python3 build.py                       # data/ + templates/ + static/ -> dist/  (fails on any unsourced fact)
BASE_URL=https://your-domain.is python3 build.py   # canonical URLs, sitemap, robots, llms.txt, CNAME use this (default: data/site.json base_url = https://icelandcampsites.com)
python3 check.py                       # (BASE_URL path-prefix aware) internal links/anchors, tag balance, <title>/description/canonical/viewport, sitemap
python3 -m http.server -d dist 8000    # preview at http://localhost:8000/
python3 make_preview.py                # standalone guide with CSS inlined -> south-coast-winter-preview.html
/tmp/pwvenv/bin/python screenshot.py [page ...]   # full-page PNGs at 390 + 1280 px -> screenshots/<page>-mobile|desktop.png (warns on horizontal overflow)
#   (venv: python3 -m venv /tmp/pwvenv && /tmp/pwvenv/bin/pip install playwright; uses /usr/bin/google-chrome)
```

Exit codes: `build.py` and `check.py` exit non-zero on failure. A nightly run should be: edit data → `./deploy.sh` (which runs every check).
`python3 serve_check.py` serves dist under the base path (`/` for icelandcampsites.com; a prefix like /iceland-campsites/ also works) and crawls every link + sitemap URL.

## Layout

```
data/site.json               site name, base_url, regions (8), themes (2)
data/campsites/<slug>.json   one file per campsite -> dist/campsites/<slug>/index.html
data/guides/<slug>.json      editorial guides       -> dist/guides/<slug>/index.html
data/tours.json              affiliate tour links (Viator, Guide to Iceland) referenced by optional "tours": [ids] in guides/campsites/regions
templates/base.html          page shell (string.Template: $title $description $canonical $body $root ...)
static/style.css             the only stylesheet (system fonts, no web fonts, no framework)
static/filter.js             ~1 KB progressive-enhancement filters for /campsites/ (page works fully without it)
static/favicon.svg           inline-style SVG logo
data/geo/iceland-outline.json  Natural Earth 50m Iceland coastline (public domain) used for the inline SVG maps
build.py, check.py, make_preview.py, screenshot.py
scripts/gen_llms.py          generates dist/llms.txt (llmstxt.org); imported and run by build.py on every build; standalone: python3 scripts/gen_llms.py
scripts/seed_south_coast_2026-10-23.py   one-off generator used for the 13 South Coast entries (kept for provenance)
dist/                        build output (git-ignored)
```

Generated pages: home, /campsites/ (all), /campsites/<slug>/, /regions/ + 8 region hubs, /themes/ + 2 theme hubs
(open-in-winter, dump-stations), /guides/ + guides, /about/ (sources & methodology), /affiliate-disclosure/, /ai-disclosure/, 404.html,
sitemap.xml, robots.txt, llms.txt (H1 + blockquote, then Guides, Campsites by region, Hubs, About this site, Optional;
descriptions only from page <title>/meta description or data fields; any sitemap URL not placed in a section falls into Optional).
check.py fails if llms.txt is missing, a link is outside BASE_URL or has no built page, or a sitemap URL is not listed; serve_check.py fetches it and its links. Region and theme hubs fill in automatically from the campsite data.

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
Facility flags: `electricity`, `showers`, `kitchen` and `dump_station` carry `"has": "yes|no|nearby|null"`. The card chips and the
/campsites/ filters use ONLY these flags (null = Unconfirmed, and a ticked filter hides it). Set `has` only from the sourced value.
Guide schema: `slug, title, short?, description, region, checked, sources{}, intro[FACT], scope_note, demand FACT, campsites[slugs],
tips[FACT], tips_title?, table? ("winter"|"overview"|"dump"|"electricity"), table_caption?, glance_title?, warning?, sections?[{id,title,paras[FACT],items[FACT]}]`.

## Design (2026-10-24 overhaul)
- Mobile-first, one stylesheet, system font stack, inline SVG only (logo, map, icons). No web fonts, no images, so no layout shift
  (map SVGs have a fixed viewBox + CSS aspect-ratio).
- Status badges: Open in winter (green) / Call ahead (amber) / Shoulder season only (orange) / Closed in winter (red) / Unconfirmed (purple).
- Maps: inline SVG of the Natural Earth outline with equirectangular projection (build.py `proj()`); markers only for campsites with
  `location.lat/lon` + `coords_src`. No tile server, no Leaflet. Each campsite page links to OpenStreetMap + Google Maps at the sourced coords.
- **Campsites without sourced coordinates (not on maps):** smaratun-fljotshlid (not found in tjalda API search 2026-10-24); mosskogar (tjalda API gives the same coords as the Mosfellsbær town site, 64.174286/-21.617192, so not trusted, 2026-10-31).
- Tables: `table.facts` and guide tables (`table.stack`) stack into label/value cards under 40rem (td `data-label`), scroll
  horizontally 40–64rem, and fit with a sticky header at ≥64rem.
- /campsites/ filters: region, winter, electricity, showers, dump station, kitchen, name search (diacritic-insensitive); state in the
  URL (`?region=south&winter=open&dump=yes`), so the home hero form (GET to /campsites/) and shareable links work. Without JS the
  form stays hidden and every card is listed.
Guide tables pull each campsite's winter/electricity/dump/adult price straight from the campsite files, so update the campsite file, not the guide.
The `electricity` table type (2026-11-02) adds an "Electricity price" column = the first price item whose label starts with "Electricity" (build.py `elec_price()`); no such item → Unconfirmed.

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
| B03 | 1 | done | campsite | skaftafell | Skaftafell Campground (full page) | south | only winter site Vík–Höfn | vatnajokulsthjodgardur.is |
| B04 | 1 | done | campsite | selfoss-gesthus | Selfoss Gesthús (full page) | south | open all year, kitchen | gesthus.is |
| B05 | 1 | done | campsite | hellisholar | Hellishólar (full page; dump?) | south | winter area G | hellisholar.is |
| B06 | 1 | done | guide | dump-stations-iceland | Where to empty a cassette toilet in Iceland (by region) | all | dump-station theme hub needs data | uos.is disposal list, icetourist.is |
| B07 | 1 | done | campsite | sandgerdi-airport-camping | Sandgerði / airport-area campsite | reykjanes | first/last night near KEF, all year | tjalda |
| B08 | 1 | done | campsite | hamrar-akureyri | Hamrar, Akureyri | north-east | all year | tjalda, hamrar.is |
| B09 | 1 | done | campsite | vogar-myvatn | Vogar, Mývatn | north-east | all year, chemical disposal | tjalda, vogarholidays.is |
| B10 | 1 | done | campsite | camp-egilsstadir | Camp Egilsstaðir | east | all year 24/7 | tjalda |
| B11 | 2 | done | guide | golden-circle-winter-campsites | Winter campsites on the Golden Circle (2026–27) | south | Úthlíð/Skjól/Geysir/Laugarvatn/Flúðir conflicts to resolve | ferdalag winter list |
| B12 | 2 | done | campsite | uthlid | Úthlíð | south | winter service list; full page 2026-11-05 | tjalda, ferdalag |
| B13 | 2 | done | campsite | skjol | Skjól (Geysir area) | south | full page 2026-11-06; winter call-ahead (own+ferdalag year-round vs Camping Card 21 May–15 Sep); tjalda inactive 2026 | own, tjalda, ferdalag, utilegukortid |
| B14 | 2 | stub | campsite | thingvellir-leirar | Þingvellir – Leirar | south | national park, winter? | thingvellir.is |
| B15 | 2 | todo | campsite | hotel-laugarvatn-camping | Laugarvatn | south | winter service list; 2026-11-04: tjalda hidden, 20 May–1 Oct, 2023 prices | ferdalag |
| B16b | 2 | stub | campsite | hraunborgir | Hraunborgir (Grímsnes) | south | added 2026-11-04 for B11; open all year per own site + tjalda; kitchen Unconfirmed | own, tjalda |
| B16 | 2 | todo | campsite | fludir | Flúðir | south | winter service list; 2026-11-04: own site 1 May–30 Sep (closed winter), adult 2,200 | ferdalag, tjalda |
| B17 | 2 | todo | campsite | hverinn-kleppjarnsreykir | Hverinn, Kleppjárnsreykir | west | hot spring site | tjalda |
| B18 | 2 | todo | campsite | stykkisholmur | Stykkishólmur | west | Snæfellsnes base | tjalda |
| B19 | 2 | todo | campsite | grundarfjordur | Grundarfjörður | west | Kirkjufell | tjalda |
| B20 | 2 | stub | campsite | mosskogar | Mosskógar (Mosfellsdalur) | capital-area | 2nd capital option | tjalda |
| B21 | 2 | stub | campsite | gardskagi | Garðskagi | reykjanes | lighthouse, near KEF | tjalda |
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
| B32 | 3 | todo | task | south-coast-stubs-dump | Confirm dump/electricity for Starlight, Farmhouse Lodge, Smáratún, Kirkjubær (Hellishólar: dump listed on Parka 2026-10-25, location/cassette use still unconfirmed) | south | Unconfirmed cells in guide B01 | email/phone needs Stefán's OK |
| B33 | 1 | done | guide | winter-campsites-iceland | Campsites Open in Winter in Iceland (all regions, 2026–27) | all | KEYWORDS #1, hub for regional winter guides | Visit Iceland camper winter service, ferdalag winter list, tjalda |
| B34 | 1 | done | guide | campsites-near-reykjavik | Campsites near Reykjavík (city, Mosfellsdalur, Hafnarfjörður) | capital-area | KEYWORDS #4 | tjalda, reykjavikcampsite.is |
| B35 | 1 | done | guide | north-iceland-winter-campsites | Winter campsites around Akureyri and Mývatn | north-east | KEYWORDS #5 | tjalda, visitakureyri.is, northiceland.is camper winter service |
| B36 | 2 | todo | guide | ring-road-campsites | Ring Road campsites in order (with map) | all | KEYWORDS #6 | tjalda coordinates |
| B37 | 2 | todo | guide | snaefellsnes-campsites | Snæfellsnes campsites | west | KEYWORDS #7 | tjalda |
| B38 | 3 | todo | guide | westfjords-campsites | Westfjords campsites | westfjords | KEYWORDS #10 | tjalda |
| B39 | 3 | todo | campsite | landmannalaugar | Landmannalaugar campsite (summer, F-road) | south | KEYWORDS #11 | fi.is |
| B40 | 1 | done | guide | campsites-with-electricity | Campsites with electric hook-up | all | KEYWORDS #13 | campsite has-flags |
| B41 | 1 | done | guide | overnight-parking-rules | Can you sleep in a campervan outside campsites in Iceland? | all | KEYWORDS #14 | Nature Conservation Act / UOS pages |
| B42 | 2 | todo | guide | campsite-prices-2026 | Iceland campsite prices 2026 (table) | all | KEYWORDS #16 | campsite data |
| B43 | 2 | todo | guide | campsites-with-hot-tubs | Campsites with hot tubs or a pool nearby | all | KEYWORDS #17 | operator pages |
| B44 | 2 | todo | guide | campsites-with-kitchen-showers-winter | Winter campsites with indoor kitchen and showers | all | KEYWORDS #18 | has-flags |
| B45 | 2 | todo | guide | campervan-iceland-november | Campervan in Iceland in November/December (campsites open) | all | KEYWORDS #19 (seasonal) | winter statuses, road.is |
| B46 | 3 | todo | guide | lodging-tax-camping | Lodging tax on campsites explained | all | KEYWORDS #20 | skatturinn.is |
| B47 | 3 | todo | guide | do-you-need-to-book-campsites | Do you need to book campsites in Iceland? | all | KEYWORDS #21 | tjalda reservation texts |
| B48 | 3 | todo | guide | parka-app-campsites | Paying for campsites with the Parka app | all | KEYWORDS #25 | parka.is |
| B50 | 2 | stub | campsite | hafnarfjordur | Hafnarfjörður (Víðistaðatún) – upgrade to full | capital-area | capital-area option with cassette disposal; summer only | reisa.is, tjalda |
| B51 | 3 | todo | task | mosfellsbaer-town-campsite | Check whether Mosfellsbær town campsite (Skólabraut) operates in 2026 | capital-area | tjalda entry hidden, 2022 prices | mos.is |
| B49 | 2 | todo | task | reykjanes-stubs-upgrade | Upgrade Reykjanes stubs; confirm dump points at Vogar and Happy Campsite | reykjanes | Unconfirmed cells in the KEF guide | operator sites; contact needs Stefán's OK |
| B52 | 2 | stub | campsite | hlid-myvatn / cja-laugar / vaglaskogur / artun | Upgrade the four North East stubs (2026-11-01) to full pages | north-east | winter facilities (Hlíð kitchen tent, CJA power) Unconfirmed | operator sites; contact needs Stefán's OK |

Done South Coast stubs (status `stub`, individual pages exist): hveragerdi-reykjamork, hella-arhus, hvolsvollur, smaratun-fljotshlid,
starlight-lambafell, skogafoss, farmhouse-lodge-skeidflot, vik-camping, kirkjubaer-ii, hofn.
Reykjanes stubs (2026-10-24, scripts/seed_reykjanes_2026-10-24.py): sandgerdi-airport-camping, gardskagi, vogar-reykjanes, happy-campsite-keflavik.
Keyword research and page ideas: KEYWORDS.md.

## Competitor & demand notes
- mapoficeland.is: competitor, **reference only, never copy text or data.**
- Reddit r/VisitingIceland: demand evidence only (fetch is blocked, so cite threads found via search results), e.g.
  https://www.reddit.com/r/VisitingIceland/comments/193fqbr/winter_campground_in_vik/ and
  https://www.reddit.com/r/VisitingIceland/comments/1gytpl5/campsite_recommendations/

## Monetization
### Active affiliate programs (approved by Stefán 2026-11-02)
| program | status | tracking (build.py adds it from data/tours.json "programs"; NEVER change) |
|---|---|---|
| Viator | ACTIVE since 2026-11-02 | `?pid=P00327922&mcid=42383&medium=link&campaign=campsites` on viator.com URLs. Never change pid or mcid; campaign must be `campsites`. |
| Guide to Iceland | ACTIVE since 2026-11-02 | `?a=1145642` (or `&a=1145642` if the URL has a query). Stated terms (theirs): 5% tours, 8% packages, 30-day cookie. |
These are the ONLY active programs; the affiliate disclosure page names only these two. Do not name rental companies there until approved and live.
How it works: `data/tours.json` = catalog of tour links (id -> program, label = heading on the target page, url without query,
checked date). Guides, campsites and regions (data/site.json) list 1-4 ids in `"tours": [...]`; build.py `tours_block()` renders a
"Tours & things to do nearby" box with the label "Affiliate links: we may earn a commission at no extra cost to you" (links to
/affiliate-disclosure/), every link `rel="sponsored noopener nofollow" target="_blank"`. Unknown ids / a query in `url` fail the build.
check.py FAILS if any viator.com link lacks pid=P00327922, mcid=42383, medium=link, campaign=campsites, any guidetoiceland.is link
lacks a=1145642, any such link lacks rel sponsored or target=_blank, or a page with such links lacks the visible label.
Viator URLs return 403 to curl/WebFetch (bot block); they were taken from search results 2026-11-02. GTI URLs fetched 200 (406 WAF on
some curl retries; confirmed via WebFetch). Do not add claims, prices or ratings next to tour links.
Placed 2026-11-02: guides south-coast-winter-campsites, campsites-near-keflavik-airport, campsites-near-reykjavik,
north-iceland-winter-campsites; campsites skaftafell, reykjavik-eco-campsite, sandgerdi-airport-camping, vogar-myvatn, hlid-myvatn,
hamrar-akureyri; regions south, capital-area, reykjanes, north-east. Golden Circle guide (B11) placed 2026-11-04: viator-golden-circle, gti-golden-circle, gti-northern-lights.

### Other programs (not active)
Site URL for applications: https://icelandcampsites.com/ (custom domain since 2026-10-27; drafts/ updated to it).
Options reviewed earlier (none of these are active; nothing else signed up by this agent):
| program | url | stated terms (from their page, not verified further) |
|---|---|---|
| Go Campers | https://www.gocampers.is/partner-with-us/ | 5% commission, ~$120 average commission per booking, 5-month cookie, 25% reader discount. 2026-10-24: Stefán sent an application email to go@gorentals.is from athafnamadurinn@mail.grokbot.com; awaiting reply |
| Campervan Iceland (2026-10-24: Stefán sent application email to info@campervaniceland.com, awaiting reply) | https://www.campervaniceland.com/affiliate-program | Stated by them, not verified (checked 2026-10-24): 5% commission per confirmed booking, 30-day cookie, payout every 6 months; sign-up via a web form. Contact info@campervaniceland.com (from /contact). Draft: drafts/campervan-iceland.md (NOT sent) |
| Camper Rental Iceland | https://www.camperrentaliceland.com/affiliates | Stated by them, not verified (checked 2026-10-24): 5% commission per completed booking, 30-day cookie; payout schedule not stated; sign-up via a web form. Contact info@camperrentaliceland.com (homepage/FAQ). Looks like a sister brand of Campervan Iceland (identical wording, both "since 2013", both at KEF); not verified. Draft: drafts/camper-rental-iceland.md (NOT sent) |
| Travel to Iceland | https://www.traveltoiceland.is/affiliate-program | Stated by them, not verified (checked 2026-10-24): 30% of net profit per completed car/camper/rooftop-tent rental, 50% after 250 confirmed bookings; 30-day cookie; payout every 6 months by PayPal or bank transfer, no minimum; dashboard + banners + API; cancelled bookings earn nothing. Contact info@traveltoiceland.is. Draft: drafts/travel-to-iceland.md (NOT sent) |
| Top picks from AFFILIATES.md (2026-10-24, stated by them, not verified, nothing signed up) | see AFFILIATES.md | |
| Northbound (marketplace, campers/motorhomes) | https://www.northbound.is/affiliate | 20% of their commission, avg ~$45/booking, 365-day attribution, payout from 10,000 ISK; form |
| Guide to Iceland | https://guidetoiceland.is/affiliates | 5% tours / 8% packages, self-drive, hotels / 15% at $5K+/mo; 30-day cookie; $100 min payout; wants a real audience. 2026-10-27 08:43 (Reykjavik): Guide to Iceland (partners@guidetoiceland.is) emailed athafnamadurinn@mail.grokbot.com "You're Approved": affiliate application approved, commission link ID 1145642 (append ?a=1145642 to any guidetoiceland.is URL, or use the $ button on their pages). Link does not expire. No new terms stated. 2026-11-02: Stefán approved using ID 1145642 on this site -> ACTIVE (see above). |
| CampEasy | https://campeasy.com/agent-portal/affiliate-links-and-coupon-codes/ | Tapfiliate; 30-day; rate not stated; paid Jan/Jul, $300 min |
| CampervanPlanet | https://www.campervanplanet.com/affiliate-program | 30% of net profit, up to 50%; self-signup |
| Discover Cars | https://www.discovercars.com/affiliate | 70% of profit + 30% Full Coverage, ~$20/booking, 365-day cookie; direct or via Travelpayouts |
| Lava Car Rental | https://affiliate.lavacarrental.is/ | 5% + 5% reader discount, 30-day; min payout 50,000 ISK |
| GetYourGuide / Viator (Viator now ACTIVE, see above; GetYourGuide not used) | partner.getyourguide.support / partnerresources.viator.com | 8% each, 31 / 30-day cookie  2026-10-24 22:02 (Reykjavik): GetYourGuide sent an account-activation email to athafnamadurinn@mail.grokbot.com (someone signed up for the Partner Program with that address; not done by this agent per records). Activation link valid 24h; not clicked. Awaiting Stefán. 2026-10-24 22:04 (Reykjavik): Viator sent a "Verify your email address" email for a new Viator Partner account at athafnamadurinn@mail.grokbot.com (verification link to partners.viator.com; not clicked, not done by this agent). Awaiting Stefán. 2026-10-24 22:33 (Reykjavik): Viator sent a reminder "Stefán Atli, please verify your Viator account" (Partner Program signup, verify button; not clicked). Same pending verification, no new terms. |
| Airalo (eSIM) | https://www.airalo.com/m/resources/airalo-affiliate-program | 10% via Impact |

## Decisions for Stefán (nothing bought)
- Domain: DONE 2026-10-27, Stefán bought icelandcampsites.com at Cloudflare; live on GitHub Pages with HTTPS (see Deploy).
  (Earlier .is ideas, not bought: icelandcampsites.is etc.; .is costs ISK 8,220/year incl. VAT per ISNIC, checked 2026-10-23.)
- Hosting: currently GitHub Pages + custom domain (free). Before heavy monetisation consider moving to Cloudflare Pages (DNS is
  already at Cloudflare) because of GitHub Pages' commercial-use policy (see AFFILIATES.md). Free-tier options: Cloudflare Pages Free (unlimited static bandwidth, 500 builds/mo; https://developers.cloudflare.com/pages/platform/limits/),
  Netlify Free ($0, 300 credits/mo hard limit; https://www.netlify.com/pricing), or GitHub Pages (free for public repos).
- Contacting campsites to fill Unconfirmed cells (email/phone) needs your approval.

## CHANGELOG
- 2026-11-06: Skjól (Geysir area) full page (/campsites/skjol/, B13). Sources checked 2026-11-06: own campsite/home/contact (skjolcenter.is), tjalda.is (not active 2026; 2025 rates), ferdalag.is camper winter service (EN + IS Ferðaþjónusta Skjótur), Camping Card 2026 opening-dates list + Skjól page. Own + ferdalag: open year-round 24/7; Camping Card: 21 May – 15 September → winter = call-ahead. 2026 published: adult (18+) 2,000, children free, showers 500 separate; no kitchen. Electricity has=yes but hook-up count conflicts (17 vs 64) and 2026 price Unconfirmed (tjalda 2025: 1,000/day). Dump has=yes from ferdalag IS Skjótur (seyrulosun); own page silent. Lodging tax, laundry, winter dump/hook-ups Unconfirmed. On Camping Card 2026 in-season. Tours: Golden Circle + northern lights. Golden Circle winter guide and all-Iceland winter guide updated for the new page. Nothing awaiting Stefán.
- 2026-11-05: Úthlíð (Biskupstungur) upgraded from stub to a full page (/campsites/uthlid/, B12). Sources checked 2026-11-05:
  operator's campsite, home, Réttin and activities pages (uthlid.icefloe.website), tjalda.is (API 'Rates 2026'), ferdalag.is
  winter list, Camping Card 2026 list. Open all year; winter = motorhome area around Réttin + pool-building toilets. 2026: adult
  2,000 (showers + hot tubs incl.), children 7–16 1,000, 0–6 free, electricity 1,000/night, tax 400/unit; drop-in only (not on
  Parka), families only (age limit 25). Indoor eating/washing-up area but no indoor kitchen listed; sludge disposal + water hose
  (own page). Not on Camping Card 2026. Réttin hours added (no season stated). Unconfirmed: laundry fee, pool hours, winter
  hook-ups/dining area/dump availability, Réttin winter hours. Tours: Golden Circle + northern lights. Nothing awaiting Stefán.
- 2026-11-04: Guide "Campsites Open in Winter on the Golden Circle (2026–27)" (/guides/golden-circle-winter-campsites/, B11)
  plus campsite stubs uthlid (B12), thingvellir-leirar (B14) and hraunborgir (new). Sources checked 2026-11-04: thingvellir.is
  camping page, uthlid.icefloe.website, hraunborgircamping.is, tjaldmidstod.is, hotelgeysir.is, skjolcenter.is, tjalda.is,
  ferdalag.is winter list. Open in winter: Þingvellir (Nyrðri-Leirar), Úthlíð, Hraunborgir. Closed: Geysir, Flúðir, Árnes.
  Unconfirmed: Laugarvatn, Skjól, Reykholt; kitchen/dump at Þingvellir, kitchen at Úthlíð and Hraunborgir, Þingvellir child price.
  Also updated winter-campsites-iceland (3 new sites in table) and south-coast scope note. Tours: Golden Circle + northern lights.
  Nothing awaiting Stefán's decision.
- 2026-11-03: Guide "Can You Sleep in a Campervan Outside Campsites in Iceland? The Rules (2026)"
  (/guides/overnight-parking-rules/, B41). Sources checked 2026-11-03: Nature Conservation Act 60/2013 on althingi.is
  (art. 5, 17, 22, 23, 31), ust.is English camping and access-rights pages (incl. protected-area list), Ferðamálastofa,
  Reykjavík police bylaw 1097/2008 art. 9 (via reykjavik.is PDF), UOS toilet-emptying page, Reddit demand thread 1o6r7kg.
  Winter table of 14 campsites on this site. Unconfirmed: fine amounts, "immediate vicinity" distance, other towns'
  police bylaws, and whether amendment l. 85/2026 (in force 1 Jan 2027) changes camping rules -> recheck in January 2027.
  No tour links on this page (not relevant). Nothing awaiting Stefán's decision.
- 2026-11-02: Affiliate links live (Stefán approved Viator with campaign=campsites and Guide to Iceland a=1145642). New
  data/tours.json + build.py tours_block(): labelled "Tours & things to do nearby" box (2-4 links, rel="sponsored noopener nofollow",
  target=_blank) on 4 guides, 6 campsites, 4 regions (list in Monetization). check.py now validates affiliate params/rel/target/label.
  Affiliate disclosure rewritten (Viator + Guide to Iceland only; no extra cost; facts unaffected; we do not review tours); About
  updated to match. Small CSS for .tours.
- 2026-11-02: Guide "Campsites with Electric Hook-up in Iceland (2026): Prices, Winter Power and Plugs"
  (/guides/campsites-with-electricity/, B40). New guide table type `electricity` (build.py `elec_price()`, CSS widths): the 25
  profiled campsites with electricity has=yes, with electricity fact, electricity price item and winter badge pulled from the
  campsite files. Key sourced facts: tjalda.is API 2026-11-02: 121 of 155 publicly listed campsites carry the 'Electricity' tag;
  2026 hook-up prices 900 ISK (Hlíð, CJA) to 2,500 ISK (Farmhouse Lodge), included at Hella Árhús, built into the pitch price at
  Reykjavík Eco (5,715 vs 3,735) and Vogar Mývatn motorhomes (1,600); per-24 h charging at Skaftafell/Egilsstaðir/Garðskagi/
  Kirkjubær. Winter power: Reykjavík Area A 16A (up to 50 vehicles), Skaftafell zones A + C, Egilsstaðir zone P 5 connections,
  Hamrar winter parking areas, Vaglaskógur none in winter; CJA/Hlíð winter power Unconfirmed. Limited hook-ups: Happy Campsite
  (3, book ahead), Hafnarfjörður (Zone B 9 pitches, long cable for Zone C). Tips: 230 V 50 Hz, sockets C/F (IEC World Plugs, seen
  via search result because iec.ch returns 403 to the box); socket types vary (Hamrar three-pin vs blue, Fossatún two/three-pin by
  area); rental cables (Rijo Campers 5 m, Kodiak cable + extension lead – cited as examples, no links to rentals beyond the
  source list, no affiliate links); hook-ups are not EV chargers (Skaftafell), CJA EV charging 35 ISK/kWh. Demand: two Reddit
  threads (seen via search). Excluded: Skógafoss and Starlight (no source lists electricity); Vík electricity price not published
  (vikcamping.is re-checked 2026-11-02, Unconfirmed). No campsite files changed. Nothing awaiting Stefán from this run (affiliate
  links remain off pending his decision).
- 2026-11-01: Guide "Winter Campsites Around Akureyri and Mývatn (2026–27)" (/guides/north-iceland-winter-campsites/, B35) with
  four new North East stubs, all from tjalda.is (+ own site / Parka / ferdalag winter list), checked 2026-11-01:
  Hlíð, Mývatn (own camping page: adult 2,700, tax 400/unit, electricity 900, showers incl.; tjalda: open all year, reception
  closed in winter → open; kitchen is a tent, winter facilities and dump point Unconfirmed; phone 781 8628 vs 899 6203, postcode
  610 vs 660); CJA, Laugar (own 'Verðskrá 2026' = tjalda: adult 1,900, unit 400 + tax 400, electricity 900; open all year, winter
  only gravel parking; heated service house, unheated kitchen; sludge disposal → dump yes); Vaglaskógur (Land og skógur; tjalda +
  Parka: winter service 15 Sep 2026 – 30 Apr 2027, campers only on car park F, 1,700/person, no electricity in winter, heated
  toilets; Parka says online booking not activated and gives 'open 3 Jun – 30 Apr' → May Unconfirmed); Ártún near Grenivík
  (tjalda: all year except Dec–Jan, adult 1,800, electricity 1,200; ferdalag: 1 May – 30 Sep, off-season on request → call-ahead;
  sludge disposal → dump yes). Winter-in-Iceland guide (B33) now includes the four in its table and drops them from the
  'not profiled' list. Excluded with summer seasons on tjalda: Húsavík, Hrafnagil (on ferdalag list), Systragil, Laugar Camping.
  New backlog row B52 (upgrade the four stubs). Nothing awaiting Stefán from this run.
- 2026-10-31: Guide "Campsites Near Reykjavík for Campervans (2026)" (/guides/campsites-near-reykjavik/, B34) with two new capital-area
  stubs: Hafnarfjörður – Víðistaðatún (tjalda + reisa.is booking page: 15 May–30 Sep, closed now; car/motorhome incl. 1 adult 3,500,
  extra adult 2,500, electricity 1,300, tax 400; Zone B 9 electric pitches, Zone C none, max 8 m; showers, washer/dryer included;
  cassette disposal listed; no indoor kitchen; Wi-Fi only at the gate) and Mosskógar, Mosfellsdalur (tjalda: 1 Mar–1 Dec → partial,
  its 'all year' flag conflicts; adult 3,000 incl. tax, electricity 2,000, kitchenette, free showers; dump listed but cassette use
  Unconfirmed; coords not used). Mosfellsbær town campsite excluded (hidden on tjalda, 2022 prices) → B51. Nothing awaiting Stefán.
- 2026-10-30: Guide "Campsites Open in Winter in Iceland (All Regions, 2026–27)" (/guides/winter-campsites-iceland/, B33). Table of all
  21 profiled campsites (winter status pulled from campsite files, incl. closed Vík/Hvolsvöllur/Happy Campsite), then the 38-entry
  ferdalag.is Camper winter service list cross-checked against tjalda.is (2026-10-30): all-year on both (Úthlíð, Hlíð Mývatn –
  reception closed in winter, CJA Laugar, Djúpivogur, Þingeyraroddi; Ártún all year except Dec–Jan); listed but tjalda gives a summer
  season (Hólmavík 15 May–15 Sep, Grettislaug Jun–Aug, Seyðisfjörður Apr–Oct, Laugarvatn 20 May–1 Oct, Flúðir May–Oct, Geysir
  15 May–15 Sep, Hvolsvöllur to 1 Nov); not active on tjalda 2026 / no dates (Skjól, Þingvellir, Fjalladýrð, Grindavík, Fossatún) and
  unmatched (Borgarfjörður Eystri, Hrafnagil, Mjóeyri, Freezer Hostel, Guesthouse Skeið) → Unconfirmed. Tips: Reykjavík Eco prebook/gate
  code, reduced winter service, umferdin.is + safetravel.is. Candidate new campsite rows from the list: Hlíð, CJA Laugar, Djúpivogur
  (B23), Þingeyraroddi (B26), Ártún. Nothing awaiting Stefán from this run.
- 2026-10-29: Camp Egilsstaðir full page – first East Iceland campsite. 2026 prices from own 'Opening hours and prices' page,
  matching tjalda.is: adult 2,950, senior/disabled 2,250, children ≤12 free, electricity 2,000/24 h, lodging tax 400/unit,
  WC + showers included, Wi-Fi free. Winter = open (own site/FAQ, tjalda, reisa, ferdalag winter list); winter zone P = car park
  with 5 electric connections; reception may be closed in low season → self-service card terminal / honesty box; winter water hose
  indoors. Dump yes (beside trash containers). Not on Camping Card (own FAQ). Conflicts noted: laundry 1,500 (price list/tjalda) vs
  1,250 (Facilities/FAQ); WCs 8 (own) vs 14 (tjalda); booking season April–October (own) vs no booking October–April (reisa);
  info-centre hours 9:00 vs 8:30 (tjalda 2025). Nothing awaiting Stefán from this run.
- 2026-10-28: Vogar, Mývatn (Vogar Travel Service) full page – second North East campsite. 2026 rates from own Camping page +
  reisa.is: adult 2,550 (tjalda.is says 2,450 – conflict shown), under-14s free, tent/car/campervan 500, motorhome 1,600 incl.
  electricity, electricity 1,100, lodging tax 400/unit, 4th night free after 3; showers + heated indoor kitchen included; no
  senior/disabled discount. Winter = open (own site/FAQ, tjalda, reisa, ferdalag winter list); no source describes reduced winter
  service → page advises calling ahead. Dump yes (black water + drinking-water hose). No reservations, QR self check-in. Not on
  Camping Card. Conflicts noted: laundry 4,990 (tjalda/reisa) vs 4,500 (FAQ); check-out before 12:00 (rules) vs none (FAQ).
  Nothing awaiting Stefán from this run.
- 2026-10-27: Custom domain https://icelandcampsites.com live (GitHub Pages, HTTPS enforced, cert for apex + www). BASE_URL and
  data/site.json base_url → https://icelandcampsites.com (no prefix); build.py writes dist/CNAME; deploy.sh sets Pages cname and
  enforces HTTPS; check.py verifies CNAME, robots.txt sitemap line, no stale github.io/example.com URLs or /iceland-campsites prefix.
  www and old github.io URLs 301 to the apex. Affiliate application drafts (drafts/, still NOT sent) now cite the new URL.
- 2026-10-27: llms.txt at the site root (<BASE_URL>/llms.txt), generated by scripts/gen_llms.py from data + built pages on every
  build (uses BASE_URL, so it follows a custom domain). New /ai-disclosure/ page (footer link, sitemap). About gained a short
  'Who runs this site' section linking both disclosures; affiliate disclosure adds 'other travel partners' (no partnerships claimed,
  still 'no affiliate links yet'). check.py + serve_check.py verify llms.txt. Nothing awaiting Stefán from this run.
- 2026-10-27: Hamrar (Kjarnaskógur, Akureyri) full page – first North East campsite. 2026 rates from tjalda.is (own site shows the
  same amounts under 'VERÐ 2025'): adult 2,500 (2,200 after first night if bought together), senior/disabled 2,100, under-18s with
  family free, unit 500, electricity 1,500, showers and lodging tax included, sleeping loft 4,400. Winter = open (own site, reisa.is,
  tjalda, ferdalag winter list) with reduced service: area A / ploughed parking areas only, staff weekdays 8–16, full service May–Oct,
  otherwise ask warden for kitchen/shower access. Dump point yes (tjalda, reisa, ferdalag). Not on Camping Card 2026 list.
  Conflicts noted: phone 461 2264 (own) vs 461 2260 (tjalda/ferdalag); postcode 600 vs 602. Jamboree 20–26 Jul 2026 special rates
  unpublished → Unconfirmed. Nothing awaiting Stefán from this run.
- 2026-10-26: Airport Camping – Sandgerði upgraded to a full page (2026 rates from tjalda + Parka: adult 2,200, senior/disabled 1,500,
  children ≤14 free, electricity 1,200, tax 400, washer 500 / wash+dry 1,000, Camping Card 100 ISK; black/grey water disposal + water
  refill → dump has=yes; no guest kitchen listed → kitchen has=no; showers yes, fee not stated). Winter status changed open → call-ahead:
  tjalda/Camping Card list (1 Jan–31 Dec)/Parka tag say all year, but Parka dates start 9 Jan, own site gives no season and it is not on
  ferdalag.is's winter service list. Own Campsite page still shows 2021 prices; Parka gives istay@istay.is vs tjalda info@airportcamping.is.
  KEF guide winter line adjusted. Nothing awaiting Stefán from this run.
- 2026-10-25: Hellishólar (Fljótshlíð) upgraded to a full page (2026 rates from tjalda + Parka: adult 3,500, senior 2,800,
  electricity 2,000, tax 400; winter = area G only, no shared kitchen; up to 40 electric pitches; Wi-Fi, laundry, dogs on leash;
  dump listed only as Parka facility tag 'Seyrulosun' → has=yes with "ask at reception"; not on Camping Card 2026 list).
  Conflicts noted on page: own Camping page shows older rates (2,600/1,700/333), Parka text says electricity 1,900, postcode 850 vs 861,
  Parka says online booking not activated. Nothing awaiting Stefán from this run.
- 2026-10-24: AFFILIATES.md – ~35 further affiliate/referral programs researched (Iceland rentals, aggregators, insurance, eSIM,
  activities, accommodation, gear, Camping Card, networks). Camping Card has no partner programme. GitHub Pages commercial-use
  policy flagged. Top picks added to Monetization. Nothing signed up or emailed.
- 2026-10-24: Design overhaul (one CSS, mobile-first cards, hero search, progressive-enhancement filters via data attributes and
  filter.js with accent-folding search, inline SVG maps from sourced coordinates with OSM/Google links, stacked responsive tables,
  winter status badges, favicon.svg, schema.org). Screenshots in screenshots/ (390 + 1280 px). Deployed and verified live (200s, new CSS).
- 2026-10-24: Keyword research in KEYWORDS.md (25 ideas, no volumes) and backlog rows B33–B49. New Reykjanes stubs: Sandgerði
  (Airport Camping), Garðskagi, Vogar (Reykjanes), Happy Campsite Keflavík (tjalda + operator pages). New guides:
  "Campsites near Keflavík Airport" and "Where to empty a campervan toilet in Iceland" (UOS rules and capital-area points,
  Visit Akureyri, icetourist list flagged as undated and in conflict with UOS on Hafnarfjörður). Grindavík excluded (no 2026 info on tjalda).
- 2026-10-24: Affiliate terms reviewed for Campervan Iceland, Camper Rental Iceland, Travel to Iceland (see Monetization).
  Application email drafts in drafts/ — NOT sent; need Stefán's approval.
- 2026-10-24: Selfoss – Gesthús upgraded to a full page (own campsite page with 2026 prices incl. hot tub 500 ISK and free parking,
  40 electric pitches, chemical disposal + drinking water, FAQ: no booking for individuals, late arrival pay next morning,
  check-out 12:00; not on the 2026 Camping Card list). Unconfirmed: laundry fee amount, child-under-12 price only on tjalda.
- 2026-10-23: Skaftafell upgraded to a full page (official VJP price list 2026, winter zones A/C, Visitor Centre hours,
  regional parking fee; whether campers pay the parking fee and the dump point location are Unconfirmed / reported only by tjalda).
- 2026-10-23: Hosting: GitHub Pages at https://iameatingalionbar.github.io/iceland-campsites/. Added `deploy.sh` and
  `serve_check.py` (serves dist under /iceland-campsites/ and crawls everything). `check.py` now strips the BASE_URL path prefix
  when mapping sitemap entries/absolute links to files. 404.html now uses base-path-absolute links.
- 2026-10-23: Project created. Stdlib build (`build.py`), checker (`check.py`), base template, CSS, 8 regions, 2 themes,
  About/methodology, affiliate-disclosure placeholder, sitemap/robots.
- 2026-10-23: Reykjavík Eco-Campsite full page (2026 prices, winter Area A rules, Klettagarðar 14 dump point).
- 2026-10-23: First guide: "Campsites Open in Winter on Iceland's South Coast (2026–27)" plus 13 South Coast campsite
  entries (12 stubs + Skaftafell/Selfoss/Hellishólar data). Screenshot + standalone preview generated.
