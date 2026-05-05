---
id: "g2-mark-vector"
title: "G2 Vector Mark"
description: |
  The vector mark draws an arrow with direction and magnitude at each data point,
  used to display field data with direction and intensity, such as wind fields and water flow directions.
  In the encode, the rotate channel controls the direction (angle), and the size channel controls the length.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "vector"
  - "vector"
  - "direction field"
  - "wind field"
  - "arrow"
  - "flow field"

related:
  - "g2-mark-point-scatter"
  - "g2-core-encode-channel"

use_cases:
  - "Wind field visualization (wind direction and speed)"
  - "Fluid dynamics simulation result display"
  - "Gradient field and force field visualization"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/point/#vector"
---

## Minimum Viable Example (Wind Field)

```javascript
import { Chart } from '@antv/g2';

// Simulated wind field data: Each grid point has position, wind direction (angle), and wind speed (magnitude)
const data = [];
for (let x = 0; x < 10; x++) {
  for (let y = 0; y < 10; y++) {
    const angle = (x * 30 + y * 15) % 360;  // Wind direction (degrees)
    const speed = 2 + Math.random() * 8;      // Wind speed
    data.push({ x, y, angle, speed });
  }
}

const chart = new Chart({ container: 'container', width: 600, height: 600 });

chart.options({
  type: 'vector',
  data,
  encode: {
    x: 'x',
    y: 'y',
    rotate: 'angle',   // Arrow rotation angle (degrees, 0=right, clockwise)
    size: 'speed',     // Arrow length (mapped to speed)
    color: 'speed',    // Color mapped to wind speed
  },
  scale: {
    color: { type: 'sequential', palette: 'viridis' },
    size: { range: [6, 24] },
  },
  style: {
    arrow: true,   // Display arrow
  },
  legend: { color: { title: 'Wind Speed (m/s)' } },
});

chart.render();
```

## Configuration Options

```javascript
chart.options({
  type: 'vector',
  data,
  encode: {
    x: 'x',
    y: 'y',
    rotate: 'direction',  // Direction angle field (0°=right, increases clockwise)
    size: 'magnitude',    // Vector length field
    color: 'intensity',   // Color encoding field (optional)
  },
  style: {
    arrow: true,          // Whether to display arrow, default true
    arrowSize: 6,         // Arrow head size (px)
  },
});
```

## Common Errors and Fixes

### Error: `rotate` is in radians, not degrees
```javascript
// ❌ If the original data is in radians, directly using the `rotate` channel will result in incorrect orientation
const data = [{ ..., direction: Math.PI / 4 }];  // radians
chart.options({ encode: { rotate: 'direction' } });  // ❌ G2 expects degrees

// ✅ Convert radians to degrees
const data = data.map(d => ({ ...d, dirDeg: (d.direction * 180) / Math.PI }));
chart.options({ encode: { rotate: 'dirDeg' } });  // ✅ degree values
```