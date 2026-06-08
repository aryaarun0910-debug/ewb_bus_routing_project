// Captures a short animated sequence of the live dashboard map (real Ladywood
// geography, animated bus routes + demand colouring) as a sequence of PNG
// frames, later assembled into docs/figures/demo.gif.
import { chromium } from "playwright";
import fs from "fs";

const OUT = "/tmp/dashboard_frames";
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 520, height: 920 } });
await page.goto("http://localhost:5175/");

// Wait for the map + first route load to settle.
await page.waitForSelector(".scenario-select", { timeout: 30000 });
await page.waitForTimeout(4000);

const FRAMES = 60;
const INTERVAL_MS = 350;
for (let i = 0; i < FRAMES; i++) {
  await page.screenshot({ path: `${OUT}/frame_${String(i).padStart(3, "0")}.png` });
  await page.waitForTimeout(INTERVAL_MS);
}

await browser.close();
console.log(`Captured ${FRAMES} frames to ${OUT}`);
