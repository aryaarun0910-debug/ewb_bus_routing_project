import { motion } from "framer-motion";

export interface Conditions {
  dayType: "weekday" | "saturday" | "sunday";
  weather: "sunny" | "cloudy" | "light_rain" | "heavy_rain";
  specialEvent: "none" | "concert" | "festival" | "market" | "road_closure" | "sports_match";
  isSchoolTerm: boolean;
}

const DAY_TYPES: Conditions["dayType"][] = ["weekday", "saturday", "sunday"];
const WEATHERS: { value: Conditions["weather"]; label: string }[] = [
  { value: "sunny", label: "Sunny" },
  { value: "cloudy", label: "Cloudy" },
  { value: "light_rain", label: "Light rain" },
  { value: "heavy_rain", label: "Heavy rain" },
];
const EVENTS: { value: Conditions["specialEvent"]; label: string }[] = [
  { value: "none", label: "None" },
  { value: "concert", label: "Concert" },
  { value: "festival", label: "Festival" },
  { value: "market", label: "Market" },
  { value: "road_closure", label: "Road closure" },
  { value: "sports_match", label: "Sports match" },
];

export default function ConditionsPanel({
  conditions,
  onChange,
}: {
  conditions: Conditions;
  onChange: (c: Conditions) => void;
}) {
  const set = <K extends keyof Conditions>(key: K, value: Conditions[K]) =>
    onChange({ ...conditions, [key]: value });

  return (
    <motion.div
      className="hud conditions-panel"
      initial={{ opacity: 0, x: -32 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
    >
      <span className="hud-eyebrow">What-if conditions</span>

      <div className="cond-group">
        <span className="cond-label">Day</span>
        <div className="cond-pills">
          {DAY_TYPES.map((d) => (
            <button
              key={d}
              className={`cond-pill${conditions.dayType === d ? " active" : ""}`}
              onClick={() => set("dayType", d)}
            >
              {d[0].toUpperCase() + d.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="cond-group">
        <span className="cond-label">Weather</span>
        <select
          className="cond-select"
          value={conditions.weather}
          onChange={(e) => set("weather", e.target.value as Conditions["weather"])}
        >
          {WEATHERS.map((w) => (
            <option key={w.value} value={w.value}>{w.label}</option>
          ))}
        </select>
      </div>

      <div className="cond-group">
        <span className="cond-label">Special event</span>
        <select
          className="cond-select"
          value={conditions.specialEvent}
          onChange={(e) => set("specialEvent", e.target.value as Conditions["specialEvent"])}
        >
          {EVENTS.map((ev) => (
            <option key={ev.value} value={ev.value}>{ev.label}</option>
          ))}
        </select>
      </div>

      <div className="cond-group cond-row">
        <label className="cond-check">
          <input
            type="checkbox"
            checked={conditions.isSchoolTerm}
            onChange={(e) => set("isSchoolTerm", e.target.checked)}
          />
          School / university term
        </label>
      </div>
    </motion.div>
  );
}
