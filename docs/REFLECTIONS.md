# Reflections — Learning Journey (UK2026-82)

> Rubric target: Criterion 3a. Score 2 requires **self-reflection from ALL team members + a shared team reflection**. Score 3 adds *how the project broadened consideration for people and planet*; score 4 adds *what worked / what we'd do differently*; score 5 adds *the importance of each design-process stage in shaping global responsibility*.
> ⚠️ **DRAFT STATUS:** The three individual sections below are scaffolds drafted from the project's actual history. Each member must edit, personalise and own their section before submission — judges can smell ghost-written reflection. The factual anchors (what happened) are real; the feelings must be yours.

---

## Team reflection (shared)

We started this project believing the hard part would be the machine learning. It wasn't. The hard part was discovering, repeatedly, that honesty is an engineering deliverable.

Three moments shaped us as a team:

**The synthetic-to-real pivot.** Our first dataset (65k rows) was entirely invented — and our R² looked great. It took us weeks to accept that a beautiful score on invented data proves nothing except self-consistency. Rebuilding the generator around real weather, a real school calendar and a real (decade-old, concessionary-only) smartcard anchor barely moved the headline number (0.940 → 0.945) — and that was the lesson: the score was never the point. *What the model learns from* is the point. We now distrust any metric we cannot trace to the world.

**The Gini coefficient that returned 0.0.** We wanted an equity headline. Our first metric gave both routing systems a perfect score — because it measured the wrong thing. The temptation was to quietly pick a metric that flattered us. Instead we documented why Gini failed, why a naive ratio failed, and what the dissimilarity index actually isolates. The gain we report (0.385 → 0.374) is modest. It is also real, and we can defend every digit of it.

**Deprecating our own work.** Jack's Unity simulation was genuinely good engineering — and we moved it to `legacy/` when the dashboard and FPGA superseded it. Choosing what the project *is* meant letting go of work we were proud of. Globally responsible engineering includes the responsibility not to ship two half-maintained things where one well-maintained thing serves better.

**What broadened our view of people and planet:** the discovery that 57.9% car-free is not a statistic about transport, it is a statistic about *time* — missed shifts, missed appointments, missed school. Every modelling decision after that (capacity floors, the no-app LED display, resident-defined constraints) was a people decision wearing an engineering costume.

**What we'd do differently:** engage CIVIC SQUARE in month one, not month four — our governance design would have been co-created instead of retrofitted; file the TfWM APC data request on day one (lead times are long, and it remains our largest open gap); and keep an assumption log from the start rather than reconstructing it at the end.

**The design process, stage by stage:** *Analyse the context* gave us the 57.9% number that re-aimed the entire project from "cool ML" to "the only option." *Define the problem* forced the realisation that the failure is structural (fixed schedules are blind), not informational. *Explore options* is where we killed our darlings — LSTM and GNN honestly outperform XGBoost on other problems, and saying so made our selection defensible. *Justify the design* is where transparency became our strategy: every number traceable to a script, every limitation disclosed before a reviewer could find it. Each stage moved the design closer to something Ladywood could own — which is what global responsibility means in practice.

---

## Arya Arun — Machine learning, demand model, analysis  *(DRAFT — personalise)*

The result I am proudest of is not R² = 0.945. It is the 0.06.

The GTFS validation returned a median Pearson correlation of 0.06 between our modelled demand shape and real service frequency — and we published it. My first instinct was that the number would sink us. Working through *why* it is low (operators set timetables for contractual and historical reasons, not measured demand) taught me more about real-world data than any high score: a weak proxy honestly reported beats a strong claim falsely made.

Building the robustness suite changed how I think about my own work. The temporal split, the anchor perturbation, the season-shift check — each one was me trying to break my own model before a judge could. The 0.0004 anchor-sensitivity spread is the single number that lets me sleep: it means our headline doesn't depend on trusting a 2010-2016 dataset's exact magnitudes.

What broadened me: realising a wrong prediction is not a residual in a loss function — at stop S06 on Dudley Road (IMD rank 312 of 32,844) it is a person in the rain. That is why the equity analysis exists as a standing check on the optimiser, not a paragraph in a report.

Next time: I would file the APC data request before writing a single line of model code, and build conformal prediction intervals in from the start instead of proposing them at the end.

## Chris Legge — Hardware, FPGA, Verilog  *(DRAFT — personalise)*

[Anchor points to write from: the WS2812B bit-bang driver and what the Quartus STA timing-closure issue taught you about claiming "it works" vs proving it; the decision to bake `route_plan.json` into ROM — accepting a snapshot display honestly rather than faking liveness; designing for a viewer with no phone, no app, no English; what the Repair Club model means for how you choose components (repairable, commodity, no vendor lock-in); what you'd do differently — e.g., starting the LoRa link-budget survey earlier.]

## Jack Booth — Simulation, Unity, multi-agent  *(DRAFT — personalise)*

[Anchor points to write from: building the multi-agent simulation that proved the routing logic before hardware existed; what it felt like when it moved to `legacy/` and why you agree (or argued) with the call; what "my work was scaffolding that let others build" means for engineering ego; the Arduino serial bridge and early integration lessons that survived into the final system; what you'd do differently.]

---
*Submission note: place the finished version in the repo as `docs/REFLECTIONS.md`, link it from the README, and carry a 60-second spoken version in the presentation (one sentence each, slide 23 moment).*
