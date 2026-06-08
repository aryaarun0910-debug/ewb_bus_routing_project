# End-of-Life & E-Waste Strategy

What happens to the hardware (FPGA hubs, LED modules, LoRa receivers, edge
compute, batteries/solar units) when it eventually fails or is superseded.
This is deliberately written with numbers, not gestures — every figure below
is sourced or explicitly flagged as our own estimate.

## 1. Why this matters at our scale

The UK generates an estimated **1.6–1.65 million tonnes of e-waste a year**
and is the world's **2nd-highest per-capita e-waste generator at ~24 kg per
person/year** ([Global E-Waste Monitor 2024, ITU/UNITAR](https://www.itu.int/en/ITU-D/Environment/Pages/Publications/The-Global-E-waste-Monitor-2024.aspx)).
Despite a mature WEEE collection system, independent analysis puts the
**true formal-recycling rate at closer to 31%** — meaning over two-thirds of
UK e-waste never passes through certified channels
([innovent-recycling.co.uk](https://www.innovent-recycling.co.uk/uk-it-recycling-statistics/)).
**That is the headline reason design-for-recovery has to be planned in from
day one rather than retrofitted**: even in a country with the regulatory
infrastructure to do this properly, most electronics still slip through the
gaps — and Ladywood is a community that cannot afford to inherit that gap on
top of everything else it already faces.

## 2. The honest scale of our footprint

| Quantity | Figure | Status |
|---|---|---|
| Electronics mass per stop unit (Pi-class SBC + LED strip + LoRa module, excl. enclosure/battery) | ~100–300 g | Our estimate, based on published component datasheets |
| Pilot deployment (15–50 stop units) total electronics mass | **~1.5–15 kg** | Our back-of-envelope calculation |
| WEEE small-producer threshold (below which simplified compliance applies) | 5,000 kg/yr | [B2B Compliance, WEEE Regulations](https://b2bcompliance.org.uk/weee-compliance/) |

Our entire pilot's end-of-life mass sits **two to three orders of magnitude
below** the regulatory threshold that triggers heavier producer-compliance
obligations. We state this plainly: at this scale, the *cost* of doing this
properly is trivial — which removes "it's too expensive to bother" as an
excuse, and is itself part of the argument for building the habit in now,
before any scale-up.

## 3. Regulatory route — what we'd actually do

Under the UK WEEE Regulations, a producer placing under 5 tonnes of
electrical/electronic equipment on the market per year can register **directly**
with the relevant environment agency rather than join a Producer Compliance
Scheme, for a flat fee of **£30/year**
([B2B Compliance](https://b2bcompliance.org.uk/weee-compliance/),
[Valpak](https://www.valpak.co.uk/weee-regulations-which-businesses-need-to-comply/)).
As a non-household (municipal/community infrastructure) deployment, we would
register on this basis — a concrete, costed compliance step rather than a
vague "we'll follow the rules" gesture.

## 4. Named local recovery partners

Rather than say "we'd partner with a recycler," here are real, certified
West Midlands Authorised Treatment Facilities (AATFs) that explicitly serve
small organisations and could realistically take this pilot's hardware at
end of life:

| Partner | Why they fit |
|---|---|
| **Enviro City Limited** (Birmingham) | Certified WEEE Authorised Treatment Facility, trading locally since 2010 ([envirocity.co.uk](https://envirocity.co.uk/)) |
| **Environmental Concern Ltd** (West Midlands) | Licensed across all 10 WEEE categories; offers small-business collection on a one-off/weekly/monthly basis ([environmental-concern.com](https://www.environmental-concern.com/)) |
| **Pure Planet Recycling** (West Midlands) | Track record serving schools, universities and local authorities — directly comparable scale to a community pilot ([pureplanetrecycling.co.uk](https://www.pureplanetrecycling.co.uk/weee-recycling-west-midlands/)) |
| **The Restart Project** (UK-wide community-repair charity) | The closest *ethos* match: a 1,000+ group network that has helped 120,000+ people repair devices, preventing an estimated 350 tonnes of waste and 3,000 tonnes CO₂e ([therestartproject.org](https://therestartproject.org/), [Parliamentary written evidence](https://committees.parliament.uk/writtenevidence/129388/pdf/)). Their "Fixing Factories" model — local, physical repair-and-recovery hubs — is a template for what a Ladywood "stop-unit repair node" could look like, run *with* rather than *for* the community. |

## 5. Modular design: build recoverability in, don't bolt it on

We take **Fairphone** as our reference precedent — not because we are
building a phone, but because it is the best-evidenced example of a small
producer designing explicitly for component recovery: the Fairphone 3 scored
**10/10 on iFixit's repairability index**, and Fairphone's stated strategy is
to double device lifetime (halving production volume) while running an
"e-waste neutral" take-back scheme that recycles one device for every one sold
([iFixit](https://www.ifixit.com/News/7292/fairphone2),
[Fairphone circularity page](https://www.fairphone.com/en/2021/11/24/product-circularity-fairphone/)).

Concretely, for our stop units this means:
- **Socketed, not soldered** modules — the LED strip, LoRa radio, and
  edge-compute board should be field-replaceable with a screwdriver, not a
  reflow oven, mirroring the board-swap pattern already validated in
  real-world LoRaWAN community-IoT pilots (e.g. the smart-water-metering
  deployment documented in [PMC7547382](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7547382/)).
- **Common-platform hardware**: by building on Pi-class SBCs (which carry an
  expected **7–10+ year operational lifespan** under low thermal/power stress —
  [designlife-cycle.com](http://www.designlife-cycle.com/raspberry-pi)), a
  failed unit's *enclosure, power system and mounting* can outlive several
  generations of the compute/radio module inside it.
- **A standard take-back slot** at each redeployment or upgrade cycle — when
  a unit is swapped for a newer revision, the old one goes directly into the
  Restart-Project-style repair/recovery loop above, not a drawer.

## 6. A gap we are choosing to fill, not hide

We searched specifically for a published smart-city or community-IoT pilot
that documents a formal end-of-life plan for its hardware, and **could not
find one** — the closest analogues are Fairphone (a commercial product, not a
civic deployment) and the Restart Project's general repair infrastructure
(not tied to a specific pilot's hardware). We are stating this honestly rather
than implying a precedent that doesn't exist: **writing this plan before
deployment, at a scale where it costs us almost nothing to get right, is
itself a small contribution to a documentation gap in this field** — not just
box-ticking for a reviewer.
