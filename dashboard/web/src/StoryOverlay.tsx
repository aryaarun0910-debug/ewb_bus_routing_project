import { motion, AnimatePresence } from "framer-motion";
import { STORY } from "./story";

export default function StoryOverlay({
  active,
  step,
  onNext,
  onPrev,
  onExit,
}: {
  active: boolean;
  step: number;
  onNext: () => void;
  onPrev: () => void;
  onExit: () => void;
}) {
  if (!active) return null;
  const s = STORY[step];
  const isLast = step === STORY.length - 1;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={step}
        className="hud story-card"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -12 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="story-progress">
          {STORY.map((_, i) => (
            <span key={i} className={`story-dot${i === step ? " active" : ""}${i < step ? " done" : ""}`} />
          ))}
        </div>
        <span className="hud-eyebrow">Step {step + 1} of {STORY.length}</span>
        <h2>{s.title}</h2>
        <p>{s.caption}</p>
        <div className="story-controls">
          <button className="story-btn ghost" onClick={onExit}>Exit</button>
          <span className="legend-spacer" />
          <button className="story-btn ghost" onClick={onPrev} disabled={step === 0}>Back</button>
          {isLast ? (
            <button className="story-btn primary" onClick={onExit}>Finish</button>
          ) : (
            <button className="story-btn primary" onClick={onNext}>Next →</button>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
