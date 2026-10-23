import json
D="2026-10-23"
FW={"title":"Ferdalag.is (Icelandic Tourist Board) – Camper winter service","url":"https://www.ferdalag.is/en/accommodation/in-tent-or-caravan/camper-winter-service","checked":D}
VIW={"title":"Visit Iceland – Camper winter service in South Iceland","url":"https://www.visiticeland.com/things-to-do/south/accommodation/camper-winter-service/","checked":D}
def tj(slug,name): return {"title":f"Tjalda.is – {name} listing (2026 rates & services)","url":f"https://tjalda.is/en/campsite/{slug}","checked":D}
U=lambda note: {"value":None,"note":note}
F=lambda v,*s: {"value":v,"src":list(s)}
sites=[]
def site(slug,name,town,lat,lon,addr,sources,season,winter,prices_label,items,facts,intro,coords=["tjalda"]):
    base={k:U("Not stated in the sources checked.") for k in ["electricity","kitchen","showers","toilets","wifi","laundry","camping_card","contact"]}
    base["dump_station"]={"has":None,"value":None,"note":"Not stated in the sources checked."}
    base.update(facts)
    sites.append({"slug":slug,"name":name,"region":"south","town":town,"completeness":"stub","checked":D,
      "sources":sources,"intro":intro,
      "location":{"address":addr,"lat":lat,"lon":lon,"coords_src":coords},
      "season":season,"winter":winter,
      "prices":{"applies_to":prices_label,"currency":"ISK","items":items},
      "facts":base,"practical":[]})
NOCARD=lambda: U("Not checked against the Camping Card list yet.")
# 1 Hveragerði
site("hveragerdi-reykjamork","Hveragerði Campsite (Reykjamörk)","Hveragerði",63.998989,-21.181625,F("Reykjamörk, 810 Hveragerði","tjalda"),
 {"tjalda":tj("hveragerdi","Hveragerði – Reykjamörk")},
 F("Tagged 'Open all year' on tjalda.is; no season dates are given in the text","tjalda"),
 {"status":"call-ahead","value":"Tjalda.is tags it 'Open all year' but gives no winter season or winter service details. Call ahead.","src":["tjalda"]},
 F("2026 rates","tjalda"),
 [{"label":"Adult per night","value":"2,300 ISK","src":["tjalda"]},{"label":"Children 0–15","value":"Free","src":["tjalda"]},
  {"label":"Electricity per night (paid on site)","value":"1,500 ISK","src":["tjalda"]},{"label":"Lodging tax per unit per night","value":"400 ISK","src":["tjalda"]},
  {"label":"Washing machine / tumble dryer (paid on site)","value":"800 ISK each","src":["tjalda"]},{"label":"Vehicle","value":None,"note":"No separate vehicle fee listed."}],
 {"electricity":F("Yes (1,500 ISK/night)","tjalda"),"showers":F("Yes – in the service house; not stated whether paid","tjalda"),"toilets":F("Yes","tjalda"),
  "kitchen":F("Listed: cooking facilities; outdoor shelter with hot/cold water for dishes and large barbecues","tjalda"),
  "laundry":F("Washing machine and tumble dryer, 800 ISK each","tjalda"),
  "dump_station":{"has":"yes","value":"Yes – 'Waste disposal for mobile homes' listed","src":["tjalda"]},
  "contact":F("+354 844 6617 · hveragerdicampsite@gmail.com","tjalda")},
 F("A municipal campsite in central Hveragerði, the first town east of Reykjavík on the Ring Road. Tjalda.is lists electricity, laundry and waste disposal for motorhomes.","tjalda"))
# 2 Selfoss Gesthús
site("selfoss-gesthus","Selfoss Campsite – Gesthús","Selfoss",63.933913,-20.992174,F("Engjavegur 56, 800 Selfoss","tjalda","ferdalag-winter"),
 {"own":{"title":"Gesthús Selfoss – home page","url":"https://www.gesthus.is/","checked":D},"tjalda":tj("gesthus","Selfoss – Gesthús"),"ferdalag-winter":FW,"visiticeland-winter":VIW},
 F("Open all year round (campsite and RV park)","own","tjalda"),
 {"status":"open","value":"Open all year. The service centre is open until 20:00 in winter (22:00 in summer).","src":["own","visiticeland-winter"]},
 F("2026 rates","tjalda"),
 [{"label":"Adult per night","value":"3,000 ISK","src":["tjalda"]},{"label":"Senior per night","value":"2,500 ISK","src":["tjalda"]},
  {"label":"Children 12 and under","value":"Free","src":["tjalda"]},{"label":"Children 13–17","value":"1,500 ISK","src":["tjalda"]},
  {"label":"Electricity per night","value":"1,900 ISK","src":["tjalda"]},{"label":"Accommodation tax per unit per night","value":"400 ISK","src":["tjalda"]},
  {"label":"Vehicle","value":None,"note":"No separate vehicle fee listed."}],
 {"electricity":F("Yes – separate area for motorhomes and folding campers with electricity (1,900 ISK/night)","tjalda"),
  "kitchen":F("Yes – service centre with kitchen and a big dining room","own","tjalda"),"showers":F("Hot showers in the service centre; not stated whether included","own"),
  "toilets":F("Yes","own"),"wifi":F("Free WiFi","tjalda"),"laundry":F("Washing machine and tumble dryer for a small fee","tjalda"),
  "dump_station":{"has":"yes","value":"Yes – 'waste disposal and other facilities for mobile homes'","src":["tjalda"]},
  "contact":F("+354 482 3585 · gesthus@gesthus.is · gesthus.is","tjalda")},
 F("A family-run campsite and RV park in the centre of Selfoss, the largest town in South Iceland, open all year with an indoor kitchen and dining room.","own","tjalda"))
# 3 Hella Árhús
site("hella-arhus","Árhús Cottage and Camping (Hella)","Hella",63.8331338,-20.4057605,F("Rangárbakki 6, 850 Hella","tjalda"),
 {"tjalda":tj("arhus","Árhús Cottage and Camping – Hella")},
 F("'Open until November/December (depending on weather)'; tjalda.is season field: 1 June – 30 November","tjalda"),
 {"status":"call-ahead","value":"Shoulder season only: 'open until November/December (depending on weather)'. Assume closed in deep winter unless the campsite confirms otherwise.","src":["tjalda"]},
 F("2026 rates","tjalda"),
 [{"label":"Adult (15+) per night, lodging tax included","value":"3,000 ISK","src":["tjalda"]},{"label":"Children 6–14","value":"1,000 ISK","src":["tjalda"]},
  {"label":"Children 5 and under","value":"Free","src":["tjalda"]},{"label":"Electricity","value":"Included in the camping fee","src":["tjalda"]},
  {"label":"Vehicle","value":None,"note":"No separate vehicle fee listed."}],
 {"electricity":F("Yes – included in the camping fee","tjalda"),"showers":F("Hot showers included in the camping fee","tjalda"),"toilets":F("Yes","tjalda"),
  "kitchen":F("Common area / indoor dining facility listed; cooking facilities not stated","tjalda"),"wifi":F("WiFi in the shared facilities","tjalda"),
  "laundry":F("Washing machine listed","tjalda"),"dump_station":{"has":"yes","value":"Yes – 'Waste disposal for mobile homes' listed","src":["tjalda"]},
  "contact":F("+354 790 3277 · arhusehf@gmail.com","tjalda")},
 F("A roughly 6-hectare riverside campsite at Hella on the Ring Road. The camping fee includes showers and electricity, and no reservations are needed.","tjalda"))
# 4 Hvolsvöllur
site("hvolsvollur","Hvolsvöllur Campsite","Hvolsvöllur",63.750005,-20.238479,F("Austurvegur 4, 860 Hvolsvöllur","ferdalag-winter"),
 {"tjalda":tj("hvolsvollur","Hvolsvöllur"),"visiticeland-winter":VIW,"ferdalag-winter":FW},
 F("1 May – 1 November","tjalda"),
 {"status":"closed","value":"Closed in winter: tjalda.is gives the season as 1 May – 1 November. Note that Visit Iceland still lists it under 'Camper winter service' – a conflict between sources, so do not rely on it between November and April.","src":["tjalda","visiticeland-winter"]},
 F("2026 rates","tjalda"),
 [{"label":"Adult per night (lodging tax included)","value":"2,900 ISK","src":["tjalda"]},{"label":"Senior / disabled per night","value":"2,000 ISK","src":["tjalda"]},
  {"label":"Children 15 and under","value":"Free","src":["tjalda"]},{"label":"Electricity per night","value":"1,900 ISK","src":["tjalda"]},
  {"label":"Shower","value":"400 ISK per use","src":["tjalda"]},{"label":"Washing machine & dryer","value":"Free (included)","src":["tjalda"]}],
 {"electricity":F("Yes (1,900 ISK/night)","tjalda"),"showers":F("Paid – 400 ISK per use","tjalda"),"toilets":F("Yes, incl. wheelchair-accessible","tjalda"),
  "kitchen":F("Simple cooking area and dishwashing in one service building","tjalda"),"wifi":F("Yes","tjalda"),"laundry":F("Washing machine & dryer included in the fee","tjalda"),
  "dump_station":{"has":"yes","value":"Yes – service area for motorhomes and caravans; 'waste disposal for mobile homes'","src":["tjalda","ferdalag-winter"]},
  "contact":F("+354 866 8945 · astahalla@gmail.com","tjalda")},
 F("A sheltered, tree-lined campsite at the entrance to Hvolsvöllur, just off the Ring Road, established in 1980.","tjalda"))
# 5 Hellishólar
site("hellisholar","Hellishólar Campsite (Fljótshlíð)","Hellishólar, Fljótshlíð",63.724877,-20.038818,F("Hellishólar, 861 Hvolsvöllur","ferdalag-winter"),
 {"tjalda":tj("hellisholar","Hellishólar, Fljótshlíð"),"visiticeland-winter":VIW,"ferdalag-winter":FW},
 F("Open year-round","tjalda"),
 {"status":"open","value":"Open year-round. In winter only area G (by the reception and restaurant) is open, and there is no shared kitchen or dining room for campers. Book and pay before pitching ('Book First Then Camp').","src":["tjalda"]},
 F("2026 rates","tjalda"),
 [{"label":"Adult per night","value":"3,500 ISK","src":["tjalda"]},{"label":"Senior (67+)","value":"2,800 ISK","src":["tjalda"]},
  {"label":"Children 13 and under","value":"Free","src":["tjalda"]},{"label":"Electricity per night","value":"2,000 ISK","src":["tjalda"]},
  {"label":"Accommodation tax per unit per night","value":"400 ISK","src":["tjalda"]}],
 {"electricity":F("Yes (2,000 ISK/night)","tjalda"),"showers":F("Winter bathhouse showers at no extra charge","tjalda"),"toilets":F("Yes","tjalda"),
  "kitchen":F("No shared kitchen or dining room for campsite guests in winter; Hygge Restaurant & Bar open daily 18:00–21:30","tjalda"),
  "laundry":F("Washing machines and dryers listed","tjalda"),"contact":F("+354 487 8360 · hellisholar@hellisholar.is · hellisholar.is","tjalda")},
 F("A golf-and-hotel complex in the Fljótshlíð countryside, about 10 km from Hvolsvöllur, that keeps one camping area (G) open in winter. Age limit 25 unless travelling with family.","tjalda"))
# 6 Smáratún
site("smaratun-fljotshlid","Smáratún / Hotel Fljótshlíð Campsite","Fljótshlíð",None,None,F("Smáratún, 861 Hvolsvöllur","own","ferdalag-winter"),
 {"own":{"title":"Smáratún farm – home page","url":"https://smaratun.is/","checked":D},"ferdalag-winter":FW,"visiticeland-winter":VIW},
 F("'We accommodate campers all year around'","own","ferdalag-winter"),
 {"status":"open","value":"Takes campers all year round; no reservation needed.","src":["own","ferdalag-winter"]},
 U("No campsite prices found on the sources checked."),
 [{"label":"Adult per night","value":None,"note":"No published price found."},{"label":"Electricity","value":None,"note":"No published price found."}],
 {"electricity":F("Yes","own"),"kitchen":F("Common kitchen","own"),"showers":F("Yes (not stated whether paid)","own"),"toilets":F("Bathroom","own"),
  "contact":F("+354 487 1416 · smaratun@smaratun.is","ferdalag-winter")},
 F("A family farm hotel off road 261 in Fljótshlíð, about 10 minutes from Hvolsvöllur, that says it takes campers all year round.","own","ferdalag-winter"),coords=[])
# 7 Skógafoss
site("skogafoss","Skógafoss Campsite (Skógar)","Skógar",63.52145,-19.507052,F("Drangshlíðardal, 861 Hvolsvöllur (new location off Skógavegur)","tjalda"),
 {"tjalda":tj("skogafoss","Tjaldsvæðið við Skógafoss"),"visiticeland-winter":VIW,"ferdalag-winter":FW},
 F("Tjalda.is: 'Open 2026', tagged as an all-year site","tjalda"),
 {"status":"call-ahead","value":"Listed under 'Camper winter service' by Visit Iceland/Ferdalag, and tjalda.is tags it all-year with the text 'Open 2026', but no winter dates or winter services are published. The campsite has moved about 2 km from the waterfall. Call ahead.","src":["tjalda","visiticeland-winter"]},
 F("2026 rates","tjalda"),
 [{"label":"Per person per night","value":"2,100 ISK","src":["tjalda"]},{"label":"Electricity","value":None,"note":"Electricity is not listed among the 2026 facilities."}],
 {"toilets":F("Yes – basic: toilets and cold fresh water","tjalda"),"showers":U("Showers are not listed among the 2026 facilities (only toilets and cold water)."),
  "dump_station":{"has":"yes","value":"Yes – 'A disposal point for portable toilets is also available on site'","src":["tjalda"]},
  "contact":F("+354 863 8064 · dalur@emax.is · pay by QR code on the service building","tjalda")},
 F("The Skógafoss campsite has moved to a new location reached via Skógavegur and the Skógræktarfélag Rangæinga sign. It is about 2 km (20 minutes on foot) from the waterfall, with basic facilities.","tjalda"))
# 8 Starlight
site("starlight-lambafell","Starlight Campsite and Pods (Lambafell)","Lambafell, near Skógar",63.543861813921716,-19.632791102125605,F("Lambafell, 861 Hvolsvöllur","tjalda"),
 {"tjalda":tj("starlight-camping","Starlight Campsite and Pods")},
 F("'Open all year!'","tjalda"),
 {"status":"open","value":"Listed 'Open all year!' on tjalda.is.","src":["tjalda"]},
 F("2026 rates","tjalda"),
 [{"label":"Adult per night","value":"2,500 ISK","src":["tjalda"]},{"label":"Senior (67+)","value":"2,000 ISK","src":["tjalda"]},
  {"label":"Children 15 and under","value":"Free","src":["tjalda"]},{"label":"Lodging tax per unit per night","value":"400 ISK","src":["tjalda"]},
  {"label":"Electricity","value":None,"note":"Electricity is not listed among facilities or prices."}],
 {"kitchen":F("Shared kitchens","tjalda"),"showers":F("Hot showers (not stated whether paid)","tjalda"),"toilets":F("Yes","tjalda"),"wifi":F("Free WiFi","tjalda"),
  "contact":F("+354 487 1212 · info@welcome.is","tjalda")},
 F("A campsite with camping pods under Eyjafjallajökull, with zones B–D reserved for campervans and motorhomes.","tjalda"))
# 9 Farmhouse Lodge
site("farmhouse-lodge-skeidflot","Farmhouse Lodge Campsite (Skeiðflöt, near Vík)","Skeiðflöt, Mýrdalur",63.4381578214337,-19.188116704075053,F("Skeiðflöt, 871 Vík","tjalda"),
 {"tjalda":tj("farmhouse-lodge","Farmhouse Lodge – Skeiðflöt"),"own":{"title":"Farmhouse Lodge – home page","url":"https://farmhouse.is/","checked":D}},
 F("'Open all year'","tjalda"),
 {"status":"call-ahead","value":"Tjalda.is says 'Open all year', but the lodge's own site says winter opening hours 'may vary depending on the season and operational requirements'. Call ahead.","src":["tjalda","own"]},
 F("2026 rates","tjalda"),
 [{"label":"Adult (15+) per night","value":"2,500 ISK","src":["tjalda","own"]},{"label":"Electricity per night","value":"2,500 ISK","src":["tjalda"]},
  {"label":"Lodging tax per unit per night","value":"400 ISK","src":["tjalda","own"]}],
 {"electricity":F("Yes (2,500 ISK/night)","tjalda"),"showers":F("Shared bathrooms and showers","tjalda"),"toilets":F("Yes","tjalda"),
  "kitchen":F("Access to cooking facilities; covered dining area","tjalda"),"wifi":F("Yes","tjalda"),
  "contact":F("+354 625 8905 · farmhouse@farmhouse.is · farmhouse.is","tjalda")},
 F("A farm lodge west of Vík with space for about 30 tents and two parking areas for up to 25 campervans. It is the only site near Vík that says it is open all year.","tjalda"))
# 10 Vík
site("vik-camping","Vík Camping","Vík",63.419327470811744,-18.995547487569553,F("Klettsvegur 7, 870 Vík","tjalda"),
 {"own":{"title":"Vík Camping – home page (Opening hours – summer 2026)","url":"https://www.vikcamping.is/","checked":D},"tjalda":tj("vik","Vík Camping"),
  "reddit-vik":{"title":"r/VisitingIceland – 'Winter campground in Vik?' (Jan 2024, traveller discussion; seen via search result)","url":"https://www.reddit.com/r/VisitingIceland/comments/193fqbr/winter_campground_in_vik/","checked":D}},
 F("20 April – 1 November 2026","own"),
 {"status":"closed","value":"Closed in winter: 'Vik Campsite will be open from 20th of April to 1st of November 2026. In winter the campsite is closed.'","src":["own"]},
 U("No 2026 prices published on the sources checked (tjalda.is says its info may be outdated)."),
 [{"label":"Adult per night","value":None,"note":"Not published."}],
 {"electricity":F("Yes","own"),"showers":F("Yes (not stated whether paid)","own"),"toilets":F("Yes","own"),"wifi":F("Yes","own"),"kitchen":F("Dining facilities","own"),
  "laundry":F("Washing machines and tumble dryers (2019 service house)","own"),
  "dump_station":{"has":"yes","value":"Yes – facilities to empty and clean car toilets (added 2019)","src":["own"]},
  "contact":F("+354 487 1345 (summer only) · vikcamping@vikcamping.is","tjalda")},
 F("The village campsite at Vík, about 1 km from the centre. Open in summer only.","own"))
# 11 Kirkjubær II
site("kirkjubaer-ii","Kirkjubær II Campsite (Kirkjubæjarklaustur)","Kirkjubæjarklaustur",63.79284,-18.049986,F("Kirkjubæjarklaustur, 880 Kirkjubæjarklaustur","tjalda"),
 {"tjalda":tj("kirkjubaer","Kirkjubær II, Kirkjubæjarklaustri"),"own":{"title":"Kirkjubær II – home page","url":"https://kirkjubaer.com/","checked":D}},
 F("March – November","tjalda"),
 {"status":"partial","value":"Shoulder season only: open from March to November, so closed December – February.","src":["tjalda"]},
 F("2026 rates","tjalda"),
 [{"label":"Adult (13+) per night","value":"2,000 ISK","src":["tjalda"]},{"label":"Accommodation tax per unit per night","value":"400 ISK","src":["tjalda"]},
  {"label":"Electricity per 24 h","value":"1,500 ISK","src":["tjalda"]},{"label":"Shower","value":"300 ISK / 3 minutes","src":["tjalda"]},
  {"label":"Washing machine / dryer","value":"950 ISK each","src":["tjalda"]},{"label":"Children under 13","value":None,"note":"Not stated."}],
 {"electricity":F("Yes – hookups throughout (1,500 ISK/24 h)","tjalda"),"kitchen":F("Kitchen and dining area in the service building","tjalda"),
  "showers":F("Paid – 300 ISK for 3 minutes","tjalda"),"toilets":F("Ten toilets","tjalda"),"wifi":F("Free WiFi","tjalda"),"laundry":F("Washer and dryer, 950 ISK each","tjalda"),
  "contact":F("+354 894 4495 · kirkjubaer@simnet.is · kirkjubaer.com (online booking, gate opens by licence plate)","tjalda","own")},
 F("A spacious village campsite in Kirkjubæjarklaustur, next to Systrakaffi and the grocery store, halfway between Vík and Skaftafell.","tjalda"))
# 12 Skaftafell
site("skaftafell","Skaftafell Campground (Vatnajökull National Park)","Skaftafell",64.016214,-16.969221,F("Skaftafell, 785 Öræfi","tjalda"),
 {"vjp":{"title":"Vatnajökull National Park – Skaftafell campground","url":"https://www.vatnajokulsthjodgardur.is/en/areas/skaftafell/tjaldsvaedid-i-skaftafelli","checked":D},
  "vjp-area":{"title":"Vatnajökull National Park – Skaftafell area","url":"https://www.vatnajokulsthjodgardur.is/en/areas/skaftafell","checked":D},
  "tjalda":tj("skaftafell","Skaftafell"),"visiticeland-winter":VIW},
 F("Open all year","vjp","tjalda"),
 {"status":"open","value":"Open all year; only zones A and C are open in winter. There is no outdoor water until about mid-May because of frost (water is available indoors). In winter, register at the Visitor Centre.","src":["vjp","tjalda"]},
 F("2026 rates","tjalda"),
 [{"label":"Adult (17–66) per night","value":"2,800 ISK","src":["tjalda"]},{"label":"Senior / disabled per night","value":"2,300 ISK","src":["tjalda"]},
  {"label":"Children 16 and under","value":"Free","src":["tjalda"]},{"label":"Electricity per night","value":"1,500 ISK","src":["tjalda"]},
  {"label":"Showers, washer and dryer","value":"Included in the campsite fee","src":["tjalda"]}],
 {"electricity":F("Yes – 100 outlets; zones A and C (open in winter) have electricity. Not for charging vehicles.","vjp","tjalda"),
  "kitchen":F("No indoor dining or cooking facilities; dishwashing sinks next to the service buildings","vjp"),
  "showers":F("Included in the 2026 fee (tjalda.is)","tjalda"),"toilets":F("Flush toilets, wheelchair-accessible","vjp"),
  "laundry":F("Washer and dryer (included in the 2026 fee)","vjp","tjalda"),"wifi":F("Wi-Fi listed","tjalda"),
  "dump_station":{"has":"yes","value":"Yes – 'Waste disposal for mobile homes' listed","src":["tjalda"]},
  "contact":F("+354 470 8300 · skaftafell@nattura.is","tjalda")},
 F("The national park campground at Skaftafell, under Vatnajökull. It is the only campsite between Kirkjubæjarklaustur and Höfn that publishes a year-round season. No reservations; vehicles can enter only 07:00–23:00.","vjp","tjalda"))
# 13 Höfn
site("hofn","Höfn Campsite (Höfn í Hornafirði)","Höfn í Hornafirði",64.258368,-15.203018,F("Hafnarbraut 52, 780 Höfn í Hornafirði","ferdalag-hofn"),
 {"tjalda":tj("tjaldsvaedid-hofn-i-hornafirdi","Tjaldsvæðið Höfn í Hornafirði"),"ferdalag-hofn":{"title":"Ferdalag.is – Höfn Camping Ground","url":"https://www.ferdalag.is/en/service/hofn-camping-ground","checked":D},"visiticeland-winter":VIW},
 F("Open all year","tjalda","ferdalag-hofn"),
 {"status":"open","value":"Listed 'Open all year' by tjalda.is and ferdalag.is ('a quality camp site all year round'). Cottages only mid-April – 15 October.","src":["tjalda","ferdalag-hofn"]},
 F("2026 rates","tjalda"),
 [{"label":"Adult per night","value":"2,500 ISK","src":["tjalda"]},{"label":"Children 15 and under","value":"Free","src":["tjalda"]},
  {"label":"Electricity per night","value":"1,500 ISK","src":["tjalda"]},{"label":"Lodging tax per unit per night","value":"400 ISK","src":["tjalda"]},
  {"label":"Washing machine / dryer","value":"1,500 ISK each","src":["tjalda"]}],
 {"electricity":F("Yes – specific spots for mobile homes, good access to electricity","ferdalag-hofn","tjalda"),"kitchen":F("Cooking facilities","ferdalag-hofn"),
  "wifi":F("Wireless internet","ferdalag-hofn"),"laundry":F("Washing facilities (1,500 ISK per machine use)","ferdalag-hofn","tjalda"),
  "showers":F("Shower listed (not stated whether paid)","tjalda"),"toilets":F("Yes","tjalda"),
  "dump_station":{"has":"yes","value":"Yes – 'Waste tank discharge' listed","src":["ferdalag-hofn"]},
  "contact":F("+354 478 1606 · camping@simnet.is","tjalda")},
 F("The town campsite at the entrance to Höfn, the last town on the South Coast before the Eastfjords, with glacier views.","ferdalag-hofn","tjalda"))
for s in sites:
    json.dump(s,open(f"data/campsites/{s['slug']}.json","w"),ensure_ascii=False,indent=2)
print(len(sites))
