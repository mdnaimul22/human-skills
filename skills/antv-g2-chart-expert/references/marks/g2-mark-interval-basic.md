---
id: "g2-mark-interval-basic"
title: "G2 Basic Bar Chart (Interval Mark)"
description: |
  Create a basic bar chart using Interval Mark. Interval Mark is the core mark type in G2 for
  rendering bar charts, column charts, and histograms.
  This article uses the Spec mode (chart.options({})), mapping x/y/color channels via encode.

library: "g2"
version: "5.x"
category: "marks"
subcategory: "interval"
tags:
  - "bar chart"
  - "column chart"
  - "categorical data"
  - "comparison"
  - "Interval"
  - "bar"
  - "spec"
  - "options"

related:
  - "g2-mark-interval-grouped"
  - "g2-mark-interval-stacked"
  - "g2-mark-interval-normalized"
  - "g2-core-chart-init"
  - "g2-core-encode-channel"
  - "g2-scale-band"

use_cases:
  - "Compare numerical values across different categories"
  - "Display metrics such as completion volume or sales volume for various items"
  - "Show ranking data"
  - "Compare metric values across multiple dimensions"

anti_patterns:
  - "Not suitable for showing trends in continuous numerical data (use Line or Area Mark instead)"
  - "Poor readability with more than 20 categories; consider pagination or filtering"
  - "Not suitable for showing part-to-whole relationships (use stacked bar charts or pie charts instead)"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/bar/basic"
---

## Core Concepts

Interval Mark maps data to rectangular intervals:
- In Cartesian coordinates: Bar (vertical) or Column (horizontal)
- In polar coordinates: Sector (Pie Chart) or Rose Chart
- In radial coordinates: Radial Bar Chart

**Key encode channels:**
- `x`: Categorical axis, typically maps categorical fields, automatically uses Band Scale
- `y`: Numerical axis, maps numerical fields, uses Linear Scale
- `y1`: Interval endpoint, used to represent interval range (e.g., Gantt Chart)
- `color`: Color, used for visual distinction

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 640,
  height: 480,
});

chart.options({
  type: 'interval',
  data: [
    { genre: 'Sports',   sold: 275 },
    { genre: 'Strategy', sold: 115 },
    { genre: 'Action',   sold: 120 },
    { genre: 'Shooter',  sold: 350 },
    { genre: 'Other',    sold: 150 },
  ],
  encode: {
    x: 'genre',
    y: 'sold',
    color: 'genre',
  },
});

chart.render();
```

## Common Variants

### Horizontal Bar Chart (Transposed Coordinate System)

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  coordinate: { transform: [{ type: 'transpose' }] },   // Key: Transposed coordinate system
});
```

### Bar Chart with Data Labels

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold' },
  labels: [
    {
      text: 'sold',            // Display the value of which field
      position: 'outside',     // 'inside' | 'outside' | 'top-left' | 'top-right'
      style: { fontSize: 12, fill: '#333' },
    },
  ],
});
```

### Rounded Bar Chart

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold' },
  style: {
    radius: 4,               // Uniform rounded corners
    // or set individually:
    // radiusTopLeft: 4,
    // radiusTopRight: 4,
  },
});
```

### Custom Colors

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold', color: 'genre' },
  scale: {
    color: {
      range: ['#1890ff', '#2fc25b', '#facc14', '#223273', '#8543e0'],
    },
  },
});
```

### With Tooltip Configuration

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold' },
  tooltip: {
    title: 'genre',
    items: [{ field: 'sold', name: 'Sales' }],
  },
});
```

### Y-axis Starting from a Specified Value

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold' },
  scale: {
    y: { domain: [50, 400] },  // Manually set the y-axis range
  },
});
```

### Customizing Axis Titles

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold' },
  axis: {
    x: { title: 'Game Type' },
    y: { title: 'Sales (Ten Thousand Units)' },
  },
});
```

### Radial Bar Chart (Jian Fan Chart)

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold' },
  coordinate: { type: 'radial', innerRadius: 0.2 },  // Radial coordinate system
});
```

### Bar Chart with Interactive Effects

```javascript
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold' },
  interaction: {
    elementHighlight: true,  // Element highlight interaction
  },
});
```

## Spec Complete Structure Quick Reference

```javascript
chart.options({
  // Mark type
  type: 'interval',

  // Data
  data: [...],

  // Channel mapping
  encode: {
    x: 'genre',           // x-axis field
    y: 'sold',            // y-axis field
    y1: 'endValue',       // Range end field (e.g., Gantt chart)
    color: 'genre',       // Color field
    shape: 'rect',        // Shape: 'rect' | 'hollow'
  },

  // Scale
  scale: {
    y: { domain: [0, 500] },
    color: { range: ['#f00', '#00f'] },
  },

  // Coordinate transformation
  coordinate: { 
    type: 'radial', 
    innerRadius: 0.2,
    transform: [{ type: 'transpose' }] 
  },

  // Style
  style: {
    radius: 4,
    fillOpacity: 0.9,
  },

  // Data labels (note: labels is plural)
  labels: [{ text: 'sold', position: 'outside' }],

  // Tooltip
  tooltip: { title: 'genre', items: [{ field: 'sold' }] },

  // Axis
  axis: {
    x: { title: 'Game Type' },
    y: { title: 'Sales' },
  },

  // Legend
  legend: {
    color: { position: 'right' }
  },

  // Interaction
  interaction: {
    elementHighlight: true
  }
});
```

## Complete Type Reference

```typescript
// Spec type passed to chart.options() (interval part)
interface IntervalSpec {
  type: 'interval';
  data?: DataOption;
  encode?: {
    x?: string | ((d: any) => any);
    y?: string | ((d: any) => any);
    y1?: string | ((d: any) => any); // End point channel
    color?: string | ((d: any) => any);
    shape?: 'rect' | 'hollow' | 'funnel' | 'pyramid' | string;
    size?: string | number | ((d: any) => any);
    series?: string;
  };
  transform?: Array<{ type: string; [key: string]: any }>;
  scale?: {
    x?: ScaleOption;
    y?: ScaleOption;
    color?: ScaleOption;
  };
  coordinate?: { 
    type?: 'polar' | 'cartesian' | 'radial';
    innerRadius?: number;
    outerRadius?: number;
    startAngle?: number;
    endAngle?: number;
    transform?: Array<{ type: string; [key: string]: any }>;
  };
  style?: {
    radius?: number;
    radiusTopLeft?: number;
    radiusTopRight?: number;
    radiusBottomLeft?: number;
    radiusBottomRight?: number;
    fill?: string;
    fillOpacity?: number;
    stroke?: string;
    lineWidth?: number;
  };
  labels?: LabelOption[];
  tooltip?: TooltipOption;
  axis?: { x?: AxisOption; y?: AxisOption };
  legend?: { color?: LegendOption };
  interaction?: { 
    elementHighlight?: boolean | { background?: boolean; region?: boolean }; 
  };
}
```

## Common Errors and Fixes

### Error 1: Using API Chaining
```javascript
// ❌ Incorrect (G2 API chaining syntax)
chart.interval().encode('x', 'genre');

// ✅ Correct (G2 Spec syntax)
chart.options({
  type: 'interval',
  data,
  encode: { x: 'genre', y: 'sold', color: 'genre' },
});
```

### Error 2: Missing container Parameter
```javascript
// ❌ Incorrect
const chart = new Chart({ width: 640, height: 480 });

// ✅ Correct
const chart = new Chart({ container: 'container', width: 640, height: 480 });
```

### Error 3: Confusion between encode and style
```javascript
// ❌ Incorrect: style does not accept data field names
chart.options({ type: 'interval',  [...], style: { color: 'genre' } });

// ✅ Correct: Use encode for data mapping and style for fixed styles
chart.options({
  type: 'interval',
  data: [...],
  encode: { color: 'genre' },   // Data-driven
  style: { fill: '#1890ff' },   // Use style only for fixed colors
});
```

### Error 4: Writing `labels` as `label` (singular)
```javascript
// ❌ Incorrect: In Spec mode, the label field is `labels` (plural)
chart.options({ type: 'interval',  data: [...], label: { text: 'sold' } });

// ✅ Correct
chart.options({ type: 'interval', data: [...], labels: [{ text: 'sold' }] });
```

### Error 5: Handling Negative Values on the Y-Axis
```javascript
// ❌ Potential Issue: Negative value bars may exceed the plotting area
chart.options({ type: 'interval',  dataWithNegatives, encode: { y: 'value' } });

// ✅ Correct: Explicitly include the negative value range via scale.y.domain
chart.options({
  type: 'interval',
  data: dataWithNegatives,
  encode: { x: 'genre', y: 'value' },
  scale: { y: { domain: [-100, 300] } },
});
```

### Error 6: Improper Use of Radial Coordinate System
```javascript
// ❌ Incorrect: Reversed x/y mapping order in radial coordinate system
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'value', y: 'genre' },  // Should be x: genre, y: value
  coordinate: { type: 'radial' }
});

// ✅ Correct: In radial coordinate system, x corresponds to angular direction, y corresponds to radial direction
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'value' },
  coordinate: { type: 'radial' }
});
```

### Error 7: Incorrect Organization of Children Structure in Composite Views
```javascript
// ❌ Incorrect: Not using the children property of the view to compose multiple marks
chart.options({
  type: 'interval',
  data: [...],
  encode: {...}
});

// ✅ Correct: Using view to contain multiple children marks
chart.options({
  type: 'view',
  children: [
    {
      type: 'interval',
      data: [...],
      encode: {...}
    },
    {
      type: 'image',
      data: [{ src: '...' }],
      encode: { src: 'src' }
    }
  ]
});
```

### Error 8: Incorrect Encoding Field Usage in Image Mark
```javascript
// ❌ Incorrect: Image mark uses x/y to map image URL
chart.options({
  type: 'image',
  data: [{ url: 'https://example.com/image.png' }],
  encode: { x: () => 0, y: () => 0, src: 'url' }  // Should not use x/y to position the image
});

// ✅ Correct: Image mark uses src field to map image URL, combined with style to set size and position
chart.options({
  type: 'image',
  data: [{ url: 'https://example.com/image.png' }],
  encode: { src: 'url' },
  style: {
    x: '50%',   // Position relative to the container
    y: '50%',
    width: 80,
    height: 80
  }
});
```

### Error 9: Incorrect Interaction Configuration Location
```javascript
// ❌ Incorrect: Placing interaction configuration outside the mark level
chart.options({
  type: 'interval',
  data: [...],
  encode: {...},
  elementHighlight: true  // Incorrect location
});

// ✅ Correct: Interaction configuration should be placed within the interaction object
chart.options({
  type: 'interval',
  data: [...],
  encode: {...},
  interaction: {
    elementHighlight: true
  }
});
```

### Error 10: Incorrect Use of y1 Channel in Interval Charts
```javascript
// ❌ Incorrect: Mapping both start and end points to the y channel
chart.options({
  type: 'interval',
  data: [{ start: 1, end: 5 }],
  encode: { x: 'name', y: ['start', 'end'] }  // Incorrect approach
});

// ✅ Correct: Using y and y1 channels to map start and end points separately
chart.options({
  type: 'interval',
  data: [{ start: 1, end: 5 }],
  encode: { x: 'name', y: 'start', y1: 'end' }
});
```

### Error 11: Incorrect Axis Label Formatting Configuration
```javascript
// ❌ Incorrect: Using non-existent axis.labelFormatter configuration
chart.options({
  type: 'interval',
  data: [...],
  axis: {
    x: {
      labelFormatter: (task, item) => {
        const datum = item.data;
        return `${datum.stage}\n${task}`;
      }
    }
  }
});

// ✅ Correct: Using the correct label configuration method
chart.options({
  type: 'interval',
  data: [...],
  axis: {
    x: {
      labelTransform: 'rotate(30)',
      labelAutoWrap: true
    }
  }
});
```