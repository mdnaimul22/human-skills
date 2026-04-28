---
id: "g2-mark-distribution-curve"
title: "G2 Distribution Curve Chart"
description: |
  The distribution curve chart uses `type: 'line'` + `encode.shape: 'smooth'` + custom binning statistics in `data.transform` to display the frequency density distribution of continuous numerical data. It is suitable for exploring data distribution patterns and comparing multiple data distributions.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "Distribution Curve Chart"
  - "distribution curve"
  - "frequency density"
  - "normal distribution"
  - "smooth"
  - "KDE"

related:
  - "g2-mark-histogram"
  - "g2-mark-density"
  - "g2-mark-violin"

use_cases:
  - "Displaying probability density distribution of continuous numerical data"
  - "Comparing distribution patterns of multiple datasets"
  - "Data quality checks (normality tests)"

anti_patterns:
  - "Unstable results with less than 30 data points; use scatter plots or box plots instead"
  - "Discrete categorical data is not suitable for distribution curves"

difficulty: "intermediate"
completeness: "full"
created: "2025-04-01"
updated: "2025-04-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/distributioncurve"
---

## Core Concepts

**Distribution Curve Chart = `type: 'line'` + `encode.shape: 'smooth'` + Manual Binning Statistics**

G2 does not have a built-in distribution curve mark. It requires binning the raw data and calculating the frequency density before using a smooth line to plot:

```
Raw Data → Binning (bins) → Calculate Frequency Density per Bin → Smooth Line
```

If the raw data has already been processed with KDE, you can directly use `type: 'density'` + `data.transform kde`.

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  theme: 'classic',
});

chart.options({
  type: 'line',
  data: {
    value: [
      { value: 85 }, { value: 92 }, { value: 78 }, { value: 95 },
      { value: 88 }, { value: 72 }, { value: 91 }, { value: 83 },
      // ... more data (recommended 100+ entries)
    ],
    transform: [
      {
        type: 'custom',
        callback: (data) => {
          const values = data.map((d) => d.value);
          const min = Math.min(...values);
          const max = Math.max(...values);
          const binCount = 20;
          const binWidth = (max - min) / binCount;

          // Binning statistics
          const bins = Array.from({ length: binCount }, (_, i) => ({
            x0: min + i * binWidth,
            x1: min + (i + 1) * binWidth,
            count: 0,
          }));
          values.forEach((v) => {
            const idx = Math.min(Math.floor((v - min) / binWidth), binCount - 1);
            bins[idx].count++;
          });

          // Output frequency density
          const total = values.length;
          return bins.map((bin) => ({
            x: (bin.x0 + bin.x1) / 2,
            y: bin.count / total,
          }));
        },
      },
    ],
  },
  encode: {
    x: 'x',
    y: 'y',
    shape: 'smooth',   // Smooth curve
  },
  style: {
    lineWidth: 3,
    stroke: '#1890ff',
  },
  axis: {
    x: { title: 'Value' },
    y: { title: 'Frequency Density' },
  },
});

chart.render();
```

## Multiple Distribution Curve Comparison

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  theme: 'classic',
});

chart.options({
  type: 'line',
  data: {
    type: 'fetch',
    value: 'https://assets.antv.antgroup.com/g2/species.json',
    transform: [
      {
        type: 'custom',
        callback: (data) => {
          // Group by species and bin each group separately
          const groups = {};
          data.forEach((d) => {
            if (!groups[d.species]) groups[d.species] = [];
            groups[d.species].push(d.y);
          });

          const binCount = 20;
          const results = [];

          Object.entries(groups).forEach(([species, values]) => {
            const filteredValues = values.filter((v) => !isNaN(v));
            const min = Math.min(...filteredValues);
            const max = Math.max(...filteredValues);
            const binWidth = (max - min) / binCount;

            const bins = Array.from({ length: binCount }, (_, i) => ({
              x0: min + i * binWidth,
              x1: min + (i + 1) * binWidth,
              count: 0,
            }));
            filteredValues.forEach((v) => {
              const idx = Math.min(Math.floor((v - min) / binWidth), binCount - 1);
              bins[idx].count++;
            });

            const total = filteredValues.length;
            bins.forEach((bin) => {
              results.push({
                x: (bin.x0 + bin.x1) / 2,
                y: bin.count / total,
                species,
              });
            });
          });

          return results;
        },
      },
    ],
  },
  encode: {
    x: 'x',
    y: 'y',
    color: 'species',
    shape: 'smooth',
  },
  style: {
    lineWidth: 2,
    strokeOpacity: 0.8,
  },
  axis: {
    x: { title: 'Petal Length' },
    y: { title: 'Frequency Density' },
  },
  legend: {
    color: { title: 'Species', position: 'right' },
  },
});

chart.render();
```

## Use density mark instead (recommended)

When the data volume is large enough, prioritize using the built-in density mark + KDE transformation, which is more accurate than manual binning:

```javascript
chart.options({
  type: 'density',
  data: {
    type: 'inline',
    value: rawData,
    transform: [
      {
        type: 'kde',
        field: 'value',        // Field for KDE
        groupBy: ['category'], // Grouping field
        size: 30,              // Number of output points, more points for finer detail
      },
    ],
  },
  encode: {
    x: 'category',
    y: 'y',
    size: 'size',
    series: 'category',
    color: 'category',
  },
  tooltip: false,
});
```

## Common Errors and Fixes

### Error 1: Forgot to encode.shape: 'smooth'

```javascript
// ❌ Effect: Line chart with obvious jagged edges, not resembling a distribution curve
chart.options({
  type: 'line',
  data: binnedData,
  encode: { x: 'x', y: 'y' },  // ❌ Missing shape: 'smooth'
});

// ✅ Correct: smooth makes the curve smooth
chart.options({
  type: 'line',
  data: binnedData,
  encode: { x: 'x', y: 'y', shape: 'smooth' },  // ✅
});
```

### Error 2: Plotting Raw Data Directly Without Binning

```javascript
// ❌ Incorrect: Raw data points connected as a line, not a density curve
chart.options({
  type: 'line',
  data: rawData,   // ❌ No binning, just connecting scatter points
  encode: { x: 'index', y: 'value', shape: 'smooth' },
});

// ✅ Correct: Bin data in data.transform before plotting
chart.options({
  type: 'line',
  data: {
    value: rawData,
    transform: [{ type: 'custom', callback: binningFn }],
  },
  encode: { x: 'x', y: 'y', shape: 'smooth' },
});
```

### Error 3: Missing `data` Keyword

```javascript
// ❌ Error: `transform` must be placed inside the `data` object
chart.options({
  type: 'line',
  data: { value: rawData, transform: [...] },  // ❌ Isolated { } syntax error
  encode: { x: 'x', y: 'y' },
});

// ✅ Correct: Must have the `data:` key
chart.options({
  type: 'line',
  data: { value: rawData, transform: [...] },  // ✅
  encode: { x: 'x', y: 'y' },
});
```

## Distribution Curve vs. Correlation Chart Selection

| Chart | Applicable Scenario |
|------|---------|
| Distribution Curve (line + smooth) | Display continuous distribution patterns, data volume 50+ |
| Histogram | Requires precise frequency statistics, observe interval distribution |
| Density mark | Large data volume, automatic KDE estimation |
| Violin Plot | Multiple group comparisons + display statistical summary |