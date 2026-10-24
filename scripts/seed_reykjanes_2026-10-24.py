"""One-off generator for the Reykjanes / Keflavík-airport campsite entries (2026-10-24). Kept for provenance.
Data: tjalda.is public API (https://tjalda.is/api/campsites) + the operators' own pages, all fetched 2026-10-24."""
import json, os
D = "2026-10-24"
def tj(slug, name): return {"title": f"Tjalda.is – {name} listing (2026 rates & services)", "url": f"https://tjalda.is/en/campsite/{slug}", "checked": D}
U = lambda note: {"value": None, "note": note}
F = lambda v, *s: {"value": v, "src": list(s)}
def H(has, v, *s): return {"has": has, "value": v, "src": list(s)}
def HU(note): return {"has": None, "value": None, "note": note}
NS = "Not stated in the sources checked."
sites = []
def site(slug, name, town, lat, lon, addr, sources, season, winter, items, facts, intro, practical):
    base = {k: U(NS) for k in ["toilets", "wifi", "laundry", "camping_card", "contact"]}
    base.update({"electricity": HU(NS), "showers": HU(NS), "kitchen": HU(NS), "dump_station": HU(NS)})
    base.update(facts)
    sites.append({"slug": slug, "name": name, "region": "reykjanes", "town": town, "completeness": "stub", "checked": D,
                  "sources": sources, "intro": intro,
                  "location": {"address": addr, "lat": lat, "lon": lon, "coords_src": ["tjalda"]},
                  "season": season, "winter": winter,
                  "prices": {"applies_to": F("2026 rates", "tjalda"), "currency": "ISK", "items": items},
                  "facts": base, "practical": practical})

site("sandgerdi-airport-camping", "Airport Camping – Sandgerði", "Sandgerði", 64.039635, -22.697616,
     F("Byggðavegur, 245 Sandgerði", "tjalda", "own"),
     {"tjalda": tj("sandgerdi", "Airport camping – Sandgerði"),
      "own": {"title": "airportcamping.is – Campsite in Sandgerði (operator's site)", "url": "https://airportcamping.is/", "checked": D}},
     F("Open all year", "tjalda"),
     {"status": "open", "value": "Tjalda.is lists it as 'Open: All year'. The operator's own site does not state a season, so ring ahead in deep winter.", "src": ["tjalda", "own"]},
     [{"label": "Adult (15+) per person per night", "value": "2,200 ISK", "src": ["tjalda"]},
      {"label": "Seniors (67+) and disabled", "value": "1,500 ISK", "src": ["tjalda"]},
      {"label": "Children 14 and under", "value": "Free", "src": ["tjalda"]},
      {"label": "Electricity per night", "value": "1,200 ISK", "src": ["tjalda"]},
      {"label": "Overnight stay tax per unit", "value": "400 ISK", "src": ["tjalda"]},
      {"label": "Washer / washer & dryer per use", "value": "500 ISK / 1,000 ISK", "src": ["tjalda"]},
      {"label": "With Camping Card", "value": "100 ISK (not valid during the town festival)", "src": ["tjalda"]}],
     {"electricity": H("yes", "Yes – electricity for RVs (1,200 ISK/night)", "tjalda"),
      "showers": H("yes", "Yes – showers in the service house; not stated whether included", "tjalda"),
      "kitchen": HU("No guest kitchen is listed; outdoor sinks with hot and cold water are."),
      "toilets": F("Yes", "tjalda"), "wifi": F("Free WiFi", "tjalda"),
      "laundry": F("Washing machine and dryer (500 ISK wash, 1,000 ISK wash & dry; dryer alone not possible)", "tjalda"),
      "dump_station": H("yes", "Yes – 'black and grey water disposal' and water-tank refill", "tjalda"),
      "camping_card": F("Accepted – 100 ISK; not valid on the days of the town's festival", "tjalda"),
      "contact": F("+354 854 8424 · info@airportcamping.is · airportcamping.is", "tjalda", "own")},
     F("A small-town campsite in the fishing village of Sandgerði, which the operator puts 8 minutes' drive from Keflavík International Airport and about 35 minutes from the Reykjavík area. Cabins can also be rented.", "tjalda", "own"),
     [F("Tjalda.is says reservations are not possible except for large groups, so individual campers just turn up.", "tjalda"),
      F("Grocery store, ATM, swimming pool and sauna are within walking distance, according to the listing.", "tjalda")])

site("gardskagi", "Garðskagi Campsite (lighthouses)", "Garður, Suðurnesjabær", 64.082316, -22.691220,
     F("Skagabraut 100, 250 Suðurnesjabær", "tjalda"),
     {"tjalda": tj("gardskagi", "Garðskagi")},
     F("Open all year", "tjalda"),
     {"status": "open", "value": "'The campsite is open all year' (tjalda.is). It is a low-service site: no showers or indoor space in any season.", "src": ["tjalda"]},
     [{"label": "Adult per night", "value": "1,700 ISK", "src": ["tjalda"]},
      {"label": "Children 0–12", "value": "Free", "src": ["tjalda"]},
      {"label": "Electricity per 24 hours", "value": "1,000 ISK", "src": ["tjalda"]},
      {"label": "Lodging tax", "value": "400 ISK", "src": ["tjalda"]}],
     {"electricity": H("yes", "Yes – electricity for campers (1,000 ISK per 24 h)", "tjalda"),
      "showers": H("no", "No – 'There are no showers, washing machines, or indoor facilities'", "tjalda"),
      "kitchen": H("no", "No indoor kitchen; an outdoor sink for washing up with hot and cold water", "tjalda"),
      "toilets": F("24-hour toilets", "tjalda"),
      "laundry": F("None", "tjalda"),
      "dump_station": H("yes", "Yes – 'a waste disposal (dump) point'", "tjalda"),
      "contact": F("+354 893 8909 / +354 777 9847 · johann@gardskagi.com", "tjalda")},
     F("A low-service campsite on the coast between the two Garðskagi lighthouses at the tip of the Reykjanes Peninsula, next to Röstin restaurant and the Garðskagi museum.", "tjalda"),
     [F("Pay at Röstin restaurant during opening hours or online at parka.is/gardskagi. Individual tents and small groups cannot reserve; the site says there is always space.", "tjalda")])

site("vogar-reykjanes", "Vogar Camping & Chalets (Reykjanes)", "Vogar", 63.984686, -22.381076,
     F("Hafnargata 19, 190 Vogar", "tjalda", "own"),
     {"tjalda": tj("vogar", "Vogar"),
      "own": {"title": "vogarcamping.is – Camping & Chalets in Vogar (operator's site)", "url": "https://vogarcamping.is/", "checked": D}},
     F("Open all year", "tjalda", "own"),
     {"status": "open", "value": "'We are open all year round' (operator's site); tjalda.is also lists it as open all year.", "src": ["own", "tjalda"]},
     [{"label": "Adult (14+) per person per night", "value": "2,800 ISK", "src": ["tjalda", "own"]},
      {"label": "Children 13 and under", "value": "Free", "src": ["tjalda"]},
      {"label": "Electricity per night", "value": "1,800 ISK", "src": ["tjalda"]},
      {"label": "Lodging tax per unit per night", "value": "400 ISK", "src": ["tjalda"]}],
     {"electricity": H("yes", "Yes – 1,800 ISK per night (price list)", "tjalda"),
      "showers": H("yes", "Yes – 'excellent facilities, including a kitchen, showers and free Wi-Fi'", "tjalda"),
      "kitchen": H("yes", "Yes – kitchen listed in the description", "tjalda"),
      "toilets": F("Yes", "tjalda"), "wifi": F("Free WiFi", "tjalda", "own"),
      "dump_station": HU("Not listed on tjalda.is or the operator's site."),
      "contact": F("+354 777 3222 · vidsjoinn@gmail.com · vogarcamping.is", "tjalda", "own")},
     F("A campsite with chalets next to the sports centre in Vogar, a village on the Reykjanes Peninsula between Keflavík Airport and Reykjavík. Not to be confused with Vogar at Lake Mývatn.", "tjalda", "own"),
     [])

site("happy-campsite-keflavik", "Happy Campsite Keflavík", "Reykjanesbær", 63.97053, -22.50995,
     F("Stapabraut 21, 260 Reykjanesbær", "tjalda", "own"),
     {"tjalda": tj("happycampsite", "Happy Campsite Keflavík"),
      "own": {"title": "Happy Campers – Welcome to Happy Campsite Keflavik (blog post, 14.07.2021)", "url": "https://happycampers.is/welcome-to-happy-campsite-keflavik/", "checked": D}},
     F("1 May – 1 October", "tjalda"),
     {"status": "closed", "value": "Closed in winter: tjalda.is gives the season as 1 May – 1 October.", "src": ["tjalda"]},
     [{"label": "Adult per person per night", "value": "1,900 ISK", "src": ["tjalda"]},
      {"label": "Electricity per night", "value": "1,000 ISK", "src": ["tjalda"]},
      {"label": "Lodging tax per unit per night", "value": "400 ISK", "src": ["tjalda"]},
      {"label": "Children", "value": None, "note": "The operator's 2021 post says free for 16 and under; the 2026 tjalda.is price list does not mention children."}],
     {"electricity": H("yes", "Yes – zone B only, few connections (tjalda.is: 3; the 2021 post said 9); book electricity in advance", "tjalda", "own"),
      "showers": H("yes", "Yes – toilets and showers with hot and cold water", "tjalda", "own"),
      "kitchen": HU("No kitchen is listed; outdoor washbasins with cold water are."),
      "toilets": F("Yes", "tjalda", "own"), "wifi": F("Free WiFi", "tjalda", "own"),
      "dump_station": HU("Not listed on tjalda.is or the operator's post."),
      "contact": F("+354 578 7860 · info@happycampers.is", "tjalda", "own")},
     F("A small campsite next to the Happy Campers rental office in Reykjanesbær, which the operator puts 6 minutes from Keflavík Airport.", "tjalda", "own"),
     [F("Late-night arrival is possible if you pre-booked on the Parka app.", "tjalda"),
      F("Zones A and C are for campervans without electricity; zone B is for vehicles that need power.", "tjalda", "own")])

out = os.path.join(os.path.dirname(__file__), "..", "data", "campsites")
for s in sites:
    with open(os.path.join(out, s["slug"] + ".json"), "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2); f.write("\n")
    print("wrote", s["slug"])
