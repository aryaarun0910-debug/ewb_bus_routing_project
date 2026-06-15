# Reflections

> Rubric target: criterion 3a — self-reflection from all three team members plus the
> shared team reflection; people/planet broadening; what worked / what we'd change; how
> each design stage shaped how responsible the result is.
>
> **Arya's section: finalised.** Chris and Jack sections are first-pass drafts grounded
> in the real project history — events are true, feelings must be verified by the person
> who lived them before the doc is submitted.

---

## Arya Arun — Machine learning, demand model, analysis

When I first saw 0.9422, I saved the file and probably told the team something vague and
confident about the model being solid. I was wrong — not in the way you'd expect, but in
a way that matters more. The number was real. It was just the wrong question.

That score came from the synthetic dataset I built at the start, and I always knew it was
synthetic. One day of real observations expanded with patterns we could justify, then
deliberately pushed to extremes to see where it broke. A scaffold, not a building. If I'd
presented 0.9422 as our headline I'd have been showing off the scaffolding — and anyone
who dug into it would have found a model trained on data it helped construct, which is not
what impressive-looking accuracy means.

The number that actually stayed with me came later. It was 0.06.

That was the correlation between the demand shape we'd modelled and the only real-world
thing we could check it against: how often the buses actually run, from the GTFS
timetables. The first time I saw it I thought we were finished. I went home and made
dinner and came back to it and it was still 0.06. That's when I stopped looking for the
mistake and started asking what it meant. Timetables get set by contracts, by routes that
have existed for decades, by what an operator can afford — not by where the demand
actually is. A weak correlation wasn't the model failing. It was the timetable and the
real demand genuinely not being the same thing, which is half the reason this project
needs to exist at all.

We put that 0.06 front and centre. It's the decision I'm most settled about. A clean,
high number would have been easier to stand behind for ninety seconds; defending a low
one means you have to actually understand it, and I'd rather be the person who can explain
the bad number than the one hiding behind a good one.

The reason the system has two parts — a demand model and a route optimiser — rather than
one thing doing both, came from an unexpected place. The earliest thinking about the
problem looked a lot like packet routing. Each stop is a node, each bus is a carrier with
a fixed bandwidth, and the question is how to get the highest-priority traffic to the
right nodes without dropping packets. That framing immediately suggested separating
prediction from optimisation: in network routing you need to know the load before you can
route, and the same is true here. XGBoost predicts load. The CVRP consumes it.

The difficulty is that those two systems don't naturally speak the same language. XGBoost
gives you a continuous float — predicted boardings per stop per hour, conditioned on
weather, day type, and season. A capacitated VRP needs discrete, bounded demand values and
a hard constraint: the total demand assigned to any vehicle can't exceed its capacity. The
interface between them is where things broke repeatedly. Early runs had the greedy
construction filling routes with high-demand stops and leaving the hospital corridor
unserved at 23:00, because the optimiser found it efficient to ignore stops where the
model predicted low headcounts. Low predicted headcount at 11pm doesn't mean nobody needs
that bus — it means fewer people need it, and those people may need it more, not less.
That's what forced the service floor into the design: a minimum guaranteed visit per stop
regardless of what the model predicts, before the optimiser is allowed to allocate anything
else. The 2-opt local search then improved routes from the greedy seed, and what started
as a worst-case 30.2% gap above brute-force optimal came down to 1.16% on average. But
none of that would have worked if the demand signal going into it was wrong — so the
pressure on the ML model was never just about R². It was about whether the numbers were
honest enough to route real buses by.

Most of what I did after that was trying to break our own model before anyone else could.
Splitting the data by time instead of at random, moving the demand anchor twenty percent
each way, testing it across seasons. The result I keep pointing people to is the 0.0002
R² spread under that twenty-percent shift. It matters not just as a robustness number but
because of what the alternative would mean: a systematic error in the 2010–2016 anchor
isn't random noise, it falls on the same stops, the same communities. If the anchor is
wrong in a directed way, the model's mistakes are directed too. That's not a statistical
problem, that's a fairness problem.

Near the end I retrained everything to fix the weekend curve against three years of real
boardings, and while I was in there I took the crime feature out. It wasn't hurting
accuracy. But I kept turning over what it meant to feed a policing-derived number into a
model that decides where buses go in a deprived ward — and the concern isn't abstract.
High-crime-area labels in police data reflect where policing is concentrated, not
necessarily where harm is highest. A model that learns from that signal risks routing
fewer buses to the places already bearing the most burden. I couldn't justify keeping it
just because it was harmless to the headline R². Deleting something that worked, on
principle, is the part that felt most like real engineering to me — more than any score I
moved.

Somewhere in all of this the error stopped being abstract. I was looking at the residuals
one evening and I started thinking about what a wrong prediction at S06 actually means. Not
"the model underestimated demand at stop 6" — a carer standing in the rain who misses the
start of a shift. Maybe it's happened already and we don't know, because we never had the
real boarding data. That image stayed. That's why the equity check lives inside the
optimiser as a hard constraint, not in a paragraph near the conclusion, and why I knew
57.9% of the ward had no car before I'd written a line of model code. There was never a
version of this where access was something we bolted on at the end.

If I started again I'd ask for the real data on the first day instead of the third month —
almost all of the honesty in this work came from chasing data we didn't have, and I'd
rather start that chase early. And I'd build the uncertainty intervals into the model
output from the beginning, so that every number going into the optimiser carried an honest
range. Not because it would have changed the headline, but because when the optimiser is
routing buses for people who have no alternative, "approximately right" should come with a
stated margin, not just a confident decimal.

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

The thing I'm proudest of building isn't in what we're submitting now, and getting okay
with that was the real lesson.

I built the Unity simulation — the part that let us watch the idea run before any of it
was real. A static map became a fully animated, ML-driven network with buses moving inside
about two weeks, and once it worked it turned into the thing everyone else tested against:
Arya's model fed routes straight into it, and a serial bridge I wrote pushed the same data
out to Chris's LED board so the screen and the hardware always agreed. The fiddly part was
never the animation — it was the seam between Unity and Python. Getting the model's output
into the simulation reliably cost me an extra week chasing a serial link that worked four
times out of five.

That fraction matters. A link that works four times out of five doesn't fail obviously —
it fails silently. The screen would show one route, the LED board would show another, and
every test we ran in between would be testing a lie. I didn't fully clock that risk until
I was deep into the week trying to close it, and I don't think I explained to the others
exactly what would have gone wrong if I hadn't. If the serial bridge had stayed unreliable,
Chris and Arya would have been building on results from a system that was quietly
contradicting itself — and they'd have had no way to know.

Moving fast had a cost I didn't clock at the time. I was shipping features quicker than
I was writing down why I'd built them the way I had, and more than once the others had to
reverse-engineer my decisions to work alongside them. There was a specific pairing session
— I don't remember exactly when — where I watched someone try to understand a choice I'd
made and realised I couldn't explain it either, not clearly. The decision had felt obvious
when I made it, and three weeks later it was opaque to me. We fixed it by logging the
integration choices the moment we made them, in the session, instead of trying to
reconstruct them afterwards. That habit probably did more for the project than any feature
I added.

When we rebuilt the front end for the finals, the Unity sim became legacy. That stung —
you put weeks into something and watch it turn into scaffolding. But scaffolding is exactly
what it was, and I've stopped seeing that as a lesser thing. The work that lets other
people build safely is usually invisible in the final product, and a system nobody verified
end-to-end is just a demo waiting to fail in front of the people who'd actually depend on
it. The person who depends on this isn't in a position to diagnose a display that's quietly
wrong — someone standing at the Dudley Road stop with no phone, no app, and a shift
starting in twelve minutes doesn't get to say "I think the routing data is stale." They
just miss the bus. Being the one who insists on proving it works before calling it done
turned out to be a role worth wanting.

The other thing the simulation gave us: the option to throw ideas away cheaply. A bad
routing design in simulation costs nothing to discover and discard. The same discovery on
a live route costs someone a journey. We tried more bad ideas inside Unity than we'd
have dared to on the real network, and the thing we submitted is what was left after most
of them failed.

What I'd do differently: write the integration tests alongside the simulation rather than
after it, and keep a log of *why* we rejected each option, not just which one we kept. The
discarded paths are half the reasoning behind the design we landed on, and right now that
reasoning lives only in whoever was in the room at the time.

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
