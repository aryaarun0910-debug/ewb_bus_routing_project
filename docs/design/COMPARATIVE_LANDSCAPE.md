# Comparative Landscape: Where This Sits Among Real Deployed Systems

Reviewers asked us to benchmark against existing live transit-information
systems — Singapore was named specifically — and to consider where else this
kind of system could work, including places with far less transit
infrastructure than the UK. This is that comparison, done properly: real
systems, real figures, and an honest statement of what makes Ladywood's
position in this landscape genuinely distinctive (rather than us asserting
novelty and hoping nobody checks).

## 1. The high end: Singapore and London

**Singapore** runs its live bus information through **LTA DataMall**, an open
real-time API platform, and the **MyTransport.SG** app, which shows predicted
*crowdedness* per bus using a three-tier colour code (green/yellow/red), built
on machine-learned models of network link travel-times and stop dwell-times
that explicitly **incorporate zone-level weather data** — the same broad idea
as our `/api/demand` "what-if conditions" panel
([Trapeze: "Leveraging AI to future-proof Singapore's bus network"](https://trapezegroup.com.au/resources/leveraging-ai-to-future-proof-singapores-bus-network/),
[LTA DataMall](https://www.developer.tech.gov.sg/products/categories/data-and-apis/land-transport-datamall/overview)).

**London's iBus** system (Siemens-built, deployed across ~8,000 buses,
2007–09) locates each vehicle to roughly **100 m** via GPS refined with a
**Kalman filter**, reporting position/heading to a central system every
**30 seconds over GPRS**, which then computes Countdown arrival predictions
([iBus, Wikipedia](https://en.wikipedia.org/wiki/IBus_(London)),
[TCRP Synthesis 48](https://onlinepubs.trb.org/onlinepubs/tcrp/tcrp_syn_48c3.pdf)).
At the point TfL opened its live-bus API, Countdown was serving **~28,000 SMS
requests and 2.5 million web hits per working day**
([TfL, 2012](https://tfl.gov.uk/info-for/media/press-releases/2012/june/transport-for-london-issues-countdown-live-bus-arrivals-api-to-the-tfl-developers-area-and-london-data-store)).

**What both systems share, and what it costs**: both are built on top of
**Automatic Passenger Counting (APC)** and/or **Automatic Vehicle Location
(AVL)** hardware fleets. High-accuracy APC units run at roughly **98%
counting accuracy and ~$8,000 per unit**; cheaper light-barrier units achieve
>95% but miscount simultaneous boarders
([arXiv:1802.03341](https://arxiv.org/pdf/1802.03341)). Fitting a fleet of
even a few dozen vehicles with this hardware costs hundreds of thousands of
pounds before a single prediction is made — this is the structural reason
systems like ours don't already exist in places like Ladywood: **the entry
cost of the conventional approach prices out exactly the communities that
would benefit most.**

The pay-off for that investment is real and measurable: real-time passenger
information (RTPI) has been shown to lift average daily ridership by roughly
**2% (Chicago/New York, World Bank data) to 5% (Kuwait)**, cut *expected*
waiting time by **13–26%** across European deployments (Stockholm, London,
The Hague), and produce **>93% satisfaction** specifically with real-time
*screen displays* at stops — directly relevant to our LED-map concept
([Papercast, summarising World Bank/NACTO/GA Tech data](https://www.papercast.com/insights/how-real-time-passenger-information-correlates-with-increased-ridership-and-satisfaction/),
[NACTO, "Where Is My Bus?"](https://nacto.org/wp-content/uploads/10-Watkins-Where-is-my-Bus_2010.pdf)).
**The benefits of this kind of system are well-evidenced. The barrier has
never been whether it works — it's been whether it's affordable to deploy
where it's needed most.**

## 2. The low end: systems built where no formal data exists

At the opposite extreme, several projects have proven that useful transit
information can be built **from nothing**, in places with no APC, no AVL, and
often no fixed routes at all:

- **Digital Matatus** (Nairobi) — university researchers rode **130+ matatu
  routes** with GPS-enabled phones to map Nairobi's ~3.5-million-rider
  informal transit network into a modified GTFS format flexible enough to
  represent irregular stops and schedules. The resulting open dataset has
  been downloaded **5,000+ times** since 2014 and was integrated into Google
  Maps ([MIT News](https://news.mit.edu/2015/digital-matatus-project-makes-invisible-visible-0826),
  [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0966692315001878)).
- **Transport for Cairo** — contracted by the **World Bank** to map Greater
  Cairo's formal *and* informal networks using a 19-person field team with
  mobile phones and custom apps
  ([transportforcairo.com](https://transportforcairo.com/work/data/)).
- **Smart Jeepney projects (Philippines)** — multiple low-cost retrofits
  built on commodity microcontrollers, e.g. **ESP32 + u-blox NEO-6M GPS**
  ([IEEE 10725311](https://ieeexplore.ieee.org/document/10725311/)), and one
  paper — **"Jeepney Real-Time Paratransit Information Using LoRaWAN,
  Smartphone APIs and IoT"** — is close to a direct technical analogue of our
  own LoRa-link proposal, applied to an informal-transit context
  ([ResearchGate](https://www.researchgate.net/publication/389465217_Jeepney_Real-Time_Paratransit_Information_Using_LoRaWAN_Smartphone_APIs_and_IoT_An_Intelligent_Transport_System_Application)).
  Mandaue City in Cebu has gone furthest toward our own concept, pairing a
  tracking app with **physical monitor displays installed at stops**
  ([Philstar](https://www.philstar.com/the-freeman/cebu-news/2024/11/16/2400630/app-track-modern-pujs-)).

These projects prove the *demand* for this kind of information exists
wherever transit is hard to predict — but they are, almost without exception,
**data-collection projects that produce static maps**, not live, predictive,
on-street display systems. Transport for Cairo's effort took a 19-person team
and World Bank backing just to produce a map.

## 3. Where Ladywood actually sits — the gap we fill

Ladywood is neither of these things. It has **formal, scheduled bus services**
(routes 8A/8C, 80, 126 — real GTFS data, real timetables) but, like most
under-resourced UK neighbourhoods, **no APC fleet, no granular live-demand
data, and no street-level live displays** — the £8,000-per-vehicle entry cost
of the Singapore/London approach is exactly as far out of reach for Ladywood
as it is for Nairobi.

This is **the missing middle** that, as far as we have been able to establish,
nobody else is building for: a low-cost, low-power, ML-driven live display for
places that *already have* formal transit and basic connectivity, but lack
the capital-intensive hardware that high-income-city systems assume as a
starting point. Three things distinguish our approach from every system
above, in combination:

1. **FPGA/LED display hardware** — power-deterministic and far cheaper than
   the LCD/app/SMS stacks Singapore, London, and the Philippine projects rely
   on.
2. **LoRa (433 MHz)** — none of the systems surveyed above use long-range,
   low-power radio; Singapore and London use GPRS/cellular (recurring SIM
   cost, higher power draw), and the Philippine projects use Wi-Fi/cellular
   too. LoRa is arguably *better suited* than any cited precedent to a
   low-income, low-connectivity neighbourhood — not a downgrade from
   cellular, but a genuinely better-fit choice for this context.
3. **A demand model built from scratch** rather than from an existing
   APC/AVL data firehose — meaning the same approach is, in principle,
   transferable to *any* place with formal transit but no measurement
   infrastructure: precisely the gap a reviewer asked us to address when they
   raised "locations where live bus data, APC infrastructure, or formalised
   transit systems are absent."

## 4. Honest summary

We are not claiming to out-perform Singapore or London on raw prediction
accuracy — they have hardware budgets we will never have, and the literature
shows it pays off. What we are claiming, and can defend with the comparison
above, is that **we are building the version of this system that becomes
possible once you refuse to assume an £8,000-per-vehicle sensor fleet** — and
that this version is exportable to a far larger set of places (under-served UK
neighbourhoods *and*, with adaptation, lower-income transit systems
worldwide) than either end of the spectrum we surveyed.
