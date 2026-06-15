# Reflections — first-pass drafts (PERSONALISE BEFORE COMMITTING)

> These are grounded in the real history of the project. The *events* are true; the
> *feelings* must be checked by the person who lived them. Read your own, cut anything
> that isn't how you actually felt, and put your own phrasing in. Then delete this banner
> and the DRAFT tags. — Rubric target: criterion 3a (self-reflection from all three +
> the shared team reflection; people/planet broadening; what worked / what we'd change;
> and how each design stage shaped how responsible the result is).

---

## Arya Arun — Machine learning, demand model, analysis

The number I keep coming back to isn't R² = 0.9421. It's 0.06.

That was the correlation between our modelled demand shape and the only real proxy we
could find — GTFS service frequency. When it came back that low my first thought was that
it sank us, and I sat with that for a day before I understood it: timetables are set by
contracts and history, not by measured demand, so a low correlation was the *honest*
result, not a failure of the model. We published it anyway. Deciding to lead with a weak
number we could defend, instead of a strong one we couldn't, changed how I think about
what "good work" means.

Most of what I built after that was me trying to break my own model before a judge could —
the temporal split, the ±20% anchor perturbation, the season-shift test. The number that
actually lets me sleep is the 0.0002 R² spread under that perturbation: it means our
headline doesn't secretly depend on trusting a 2010–2016 dataset's exact magnitudes. Late
on, I retrained to fix the weekend curve against three years of observed data, and I
removed the crime feature even though it was harmless to accuracy — because a model for a
deprived community shouldn't take a policing-derived input it doesn't need. Choosing to
delete something that worked, on principle, felt more like engineering than any accuracy
gain.

What broadened me: a wrong prediction stopped being a residual in a loss function. At S06
on Dudley Road it's a carer in the rain who missed a shift. That's *why* the equity
analysis is a standing constraint on the optimiser and not a closing paragraph — and it's
a direct consequence of *analysing the context first*: we knew 57.9% of the ward has no
car before we wrote a line of model code, so equity was designed in, not bolted on.

What I'd do differently: file the real data request on day one instead of month three, and
build the uncertainty intervals in from the start rather than proposing them at the end.

---

## Chris Legge — Hardware, FPGA, Verilog

I learned the difference between "it compiles" and "it works" the hard way, at about 1am,
chasing a timing violation on the WS2812B driver that Quartus kept failing on. The LEDs
*looked* right on the bench but the static-timing analysis said the pulse widths weren't
guaranteed — and I'd been telling the team it was done. It wasn't done; it happened to
work. Closing that timing properly, and learning to say "verified" only when I could prove
it, is the thing I'll take into every hardware job after this.

The decision I'm most quietly proud of is an unglamorous one: baking the route plan into
ROM and accepting that the board shows an honest *snapshot*, instead of wiring up something
that faked live updates for the demo. It would have looked more impressive. It would also
have been a lie to anyone watching, and the people this display is *for* — someone at a
stop with no phone, no app, and maybe no English — are exactly the people who can't
double-check a screen that's quietly wrong. That constraint, designing for a viewer who has
to trust the thing completely, drove every choice: colour instead of words, brightness over
detail, a fail-safe that goes dark rather than show stale data.

It also changed how I pick components. Cheap, common, repairable parts aren't a compromise
here — if this is going into a community, it has to be fixable by that community, not
locked to a vendor. That's a different design goal than "best spec," and exploring the
options through *that* lens is what makes the hardware globally responsible rather than
just clever.

What I'd do differently: run the LoRa link-budget survey at the start instead of leaving
the live-radio question to the end, and write the testbench *first* — I'd have caught the
timing issue weeks earlier if I'd verified before I trusted.

---

## Jack Booth — Simulation, systems & validation, integration

My biggest contribution doesn't exist in the final design, and learning to be okay with
that was the real lesson.

I built the multi-agent simulation that let us test the routing logic before any hardware
existed — buses, stops, demand, the optimiser, all running in software so we could see
whether the idea even held together. It did its job: it proved the routing worked, it let
us explore options we'd never have risked on real hardware, and it caught problems early
and cheaply. And then, once the model and the FPGA were carrying the project, we moved it
to `legacy/`. I'll be honest — that stung at first. You put weeks into something and watch
it become scaffolding.

But that's exactly what it was, and that reframing is what broadened me: in a real team,
the work that lets *other* people build safely is often invisible in the final product, and
that doesn't make it less essential. Integration and validation are the same — nobody
applauds the route-plan check or the Arduino serial bridge, but a system that isn't
verified end-to-end is just a demo waiting to fail in front of the people who depend on it.
For a transport system that vulnerable shift-workers would actually rely on, "it probably
works" isn't good enough; somebody has to be the one who refuses to call it done until it's
proven, and I learned that's a role worth wanting.

Where it connects to responsibility: being able to *explore lots of options* in simulation,
cheaply and without consequences, is what let us reject the ideas that looked good but
served people badly — before they ever reached a street.

What I'd do differently: build the integration tests alongside the simulation instead of
after, and keep a running log of *why* we rejected each option, not just which one we kept —
the rejected paths are half the story of a responsible design.

---

## Shared team reflection

Three moments taught us more than any result.

The first was the **pivot from synthetic to real data**. We started with a fully invented
dataset because it was easy, and the honest discomfort of presenting numbers we'd made up
is what pushed us to anchor everything we could to real sources — smartcard volumes, real
weather, observed boarding shapes. The project got harder and far more defensible at the
same time.

The second was the **Gini coefficient that returned 0.0**. Our first equity metric said
the system was perfectly fair — which was obviously wrong, and chasing *why* (it was
measuring the wrong thing) led us to the dissimilarity index that actually captures whether
service reaches need. We almost reported the 0.0. Learning to distrust a flattering number
became a habit.

The third was learning to **state our limits before anyone asked**. Every reviewer
comment we got rewarded the things we'd disclosed, not the things we'd polished — so we
made disclosure the method, not the apology.

Looking back across the design process, the order mattered. *Analysing the context* first —
the no-car households, the hospital corridor, the digitally excluded — is what made equity
a constraint instead of a feature. *Defining the problem* narrowly (predict demand, route
the buses that already run) is what kept us from the app-based ideas that have failed real
communities. *Exploring options* in simulation let us reject the wrong ones cheaply. And
*justifying the final design* with logged assumptions and honest validation is what we'd
want anyone to demand of an engineer building something people have to trust. The
responsibility wasn't a stage at the end — it was decided at every step.
