import { motion, AnimatePresence } from "framer-motion";
import type { RoutesResponse } from "./api";

function summarize(r: RoutesResponse | null) {
  if (!r) return null;
  const totalDemand = r.routes.reduce((sum, route) => sum + (Number(route.total_demand) || 0), 0);
  return {
    buses: r.routes.length,
    totalDemand,
    unserved: r.unserved_stops ?? [],
  };
}

export default function ComparePanel({
  active,
  scenarios,
  scenario,
  compareScenario,
  onCompareChange,
  current,
  compare,
}: {
  active: boolean;
  scenarios: string[];
  scenario: string;
  compareScenario: string;
  onCompareChange: (s: string) => void;
  current: RoutesResponse | null;
  compare: RoutesResponse | null;
}) {
  const a = summarize(current);
  const b = summarize(compare);

  return (
    <AnimatePresence>
      {active && (
        <motion.div
          className="hud compare-panel"
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -16 }}
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
        >
          <span className="hud-eyebrow">Compare scenarios · same time window</span>
          <div className="compare-grid">
            <div className="compare-col">
              <span className="compare-name">{scenario}</span>
              {a && (
                <>
                  <Stat label="Buses deployed" value={String(a.buses)} />
                  <Stat label="Demand served" value={a.totalDemand.toFixed(0)} />
                  <Stat label="Unserved stops" value={String(a.unserved.length)} />
                </>
              )}
            </div>

            <div className="compare-col compare-col-right">
              <select
                className="cond-select compare-select"
                value={compareScenario}
                onChange={(e) => onCompareChange(e.target.value)}
              >
                {scenarios.filter((s) => s !== scenario).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              {b && (
                <>
                  <Stat label="Buses deployed" value={String(b.buses)} delta={a ? b.buses - a.buses : undefined} />
                  <Stat
                    label="Demand served"
                    value={b.totalDemand.toFixed(0)}
                    delta={a ? Math.round(b.totalDemand - a.totalDemand) : undefined}
                  />
                  <Stat
                    label="Unserved stops"
                    value={String(b.unserved.length)}
                    delta={a ? b.unserved.length - a.unserved.length : undefined}
                    invertDelta
                  />
                </>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Stat({ label, value, delta, invertDelta }: { label: string; value: string; delta?: number; invertDelta?: boolean }) {
  let deltaClass = "";
  let deltaText = "";
  if (delta !== undefined && delta !== 0) {
    const positive = invertDelta ? delta < 0 : delta > 0;
    deltaClass = positive ? "delta-up" : "delta-down";
    deltaText = `${delta > 0 ? "+" : ""}${delta}`;
  }
  return (
    <div className="compare-stat">
      <span className="stat-value">{value}</span>
      {deltaText && <span className={`stat-delta ${deltaClass}`}>{deltaText}</span>}
      <span className="stat-label">{label}</span>
    </div>
  );
}
