# Legacy

Contains the original Unity simulation built in the first phase of the project.

The simulation runs the same routing logic as the web dashboard on an abstract grid map, driving the FPGA LED display via Arduino serial. It is preserved here for reference and demonstration purposes.

The web dashboard (`dashboard/`) is the primary interface going forward.

## Contents

- `simulation/Scripts/` — Unity C# scripts (bus movement, Arduino serial bridge, ML integration)
- `simulation/StreamingAssets/` — Python scripts called at runtime by Unity
