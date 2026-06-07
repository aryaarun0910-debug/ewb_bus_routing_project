export interface StoryStep {
  title: string;
  caption: string;
  scenario: string;
  windowIdx: number;
  imdOverlay?: boolean;
  comparing?: boolean;
  compareScenario?: string;
}

export const STORY: StoryStep[] = [
  {
    title: "A Tuesday morning in Ladywood",
    caption:
      "It's 07:00. Our XGBoost model predicts how many people will board at every stop this hour — sized and coloured live on the map.",
    scenario: "Weekday (Sunny, Sep)",
    windowIdx: 1,
  },
  {
    title: "Then the storm comes",
    caption:
      "Switch the conditions to a heavy-rain November morning: demand reshapes across the network, and several areas go unserved by the available fleet.",
    scenario: "Weekday (Heavy Rain, Nov)",
    windowIdx: 1,
  },
  {
    title: "Who gets left behind?",
    caption:
      "Overlay every stop's IMD 2019 deprivation score. The areas that depend most on the bus — Ladywood is one of England's most deprived wards — are exactly the ones most exposed when service is stretched.",
    scenario: "Weekday (Heavy Rain, Nov)",
    windowIdx: 1,
    imdOverlay: true,
  },
  {
    title: "The optimiser adapts",
    caption:
      "Compare the storm scenario against an ordinary sunny day, side by side. The routing optimiser reallocates buses toward the highest-need areas as conditions change — fixed schedules can't do that.",
    scenario: "Weekday (Heavy Rain, Nov)",
    windowIdx: 1,
    imdOverlay: false,
    comparing: true,
    compareScenario: "Weekday (Sunny, Sep)",
  },
  {
    title: "Predictive routing, built on real data",
    caption:
      "Every prediction here is anchored to real Birmingham weather, real school-term calendars, and real TfWM ridership — validated on a full year of unseen 2024 data. This is what adapting to people, not timetables, looks like.",
    scenario: "Weekday (Sunny, Sep)",
    windowIdx: 5,
    comparing: false,
  },
];
