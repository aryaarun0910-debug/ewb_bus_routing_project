import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { Stop } from "./api";

const METRIC_DEFS: { label: string; def: string }[] = [
  { label: "IMD score", def: "Index of Multiple Deprivation (2019) for the stop's Lower Super Output Area — higher means more deprived. England's official measure of relative deprivation, combining income, employment, health, education, crime, housing, and environment." },
  { label: "Points of interest", def: "Count of nearby amenities (shops, services, civic buildings) from OpenStreetMap — a proxy for footfall and local activity around the stop." },
  { label: "Population", def: "Estimated resident population in the stop's surrounding LSOA (ONS Census-derived), indicating the size of the community the stop serves." },
  { label: "Crime (2024)", def: "Total recorded crime incidents in the stop's local area for 2024 (police.uk data) — higher values may indicate need for safer, more frequent service in the evenings." },
  { label: "Elevation", def: "Height above sea level in metres — included as a feature because hills affect walking distance to stops and journey times." },
];

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

const fmt = (v: number | null | undefined, digits = 0) =>
  v === null || v === undefined ? "—" : v.toFixed(digits);

export default function StopPanel({
  stop,
  boardings,
  onClose,
}: {
  stop: Stop | null;
  boardings: number;
  onClose: () => void;
}) {
  const [showGlossary, setShowGlossary] = useState(false);

  return (
    <AnimatePresence>
      {stop && (
        <motion.aside
          key={stop.stop_id}
          className="hud stop-panel"
          initial={{ opacity: 0, x: 32 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 32 }}
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
        >
          <button className="panel-close" onClick={onClose} aria-label="Close">
            ×
          </button>
          <span className="hud-eyebrow">{stop.stop_id} · {stop.importance}</span>
          <h2>{stop.name}</h2>
          <p className="panel-note">{stop.note}</p>

          <div className="stat-grid">
            <Stat label="Predicted boardings" value={fmt(boardings)} />
            <Stat label="IMD score" value={fmt(stop.imd_score, 1)} />
            <Stat label="Points of interest" value={fmt(stop.poi_total)} />
            <Stat label="Population" value={fmt(stop.population)} />
            <Stat label="Crime (2024)" value={fmt(stop.crime_total_2024)} />
            <Stat label="Elevation" value={stop.elevation_m == null ? "—" : `${fmt(stop.elevation_m)} m`} />
          </div>

          <button className="glossary-toggle" onClick={() => setShowGlossary((v) => !v)}>
            {showGlossary ? "Hide metric definitions ▴" : "What do these metrics mean? ▾"}
          </button>
          <AnimatePresence>
            {showGlossary && (
              <motion.dl
                className="glossary"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
              >
                {METRIC_DEFS.map((m) => (
                  <div key={m.label} className="glossary-entry">
                    <dt>{m.label}</dt>
                    <dd>{m.def}</dd>
                  </div>
                ))}
              </motion.dl>
            )}
          </AnimatePresence>

          <div className="panel-routes">
            <span className="hud-eyebrow">Served by</span>
            <div className="route-chips">
              {stop.routes.map((r) => (
                <span key={r} className="route-chip">Route {r}</span>
              ))}
            </div>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
