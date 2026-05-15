---
id: "g2-concept-chart-selection"
title: "G2 Chart Type Selection Guide"
description: |
  Choose the appropriate chart type based on data characteristics and analysis objectives.
  Covers six major scenarios: comparison, trend, proportion, distribution, and relationship,
  with corresponding G2 implementation methods to help avoid the common mistake of "using the wrong chart."

library: "g2"
version: "5.x"
category: "concepts"
tags:
  - "图表选择"
  - "chart selection"
  - "可视化设计"
  - "bar chart"
  - "line chart"
  - "pie chart"
  - "scatter plot"
  - "decision-making"

related:
  - "g2-concept-visual-channels"
  - "g2-mark-interval-basic"
  - "g2-mark-line-basic"
  - "g2-mark-arc-pie"
  - "g2-mark-point-scatter"

use_cases:
  - "Select the correct chart type based on user requirements"
  - "Avoid using pie charts or line charts in inappropriate scenarios"
  - "Understand when to use G2 charts vs G6 graph analysis"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
---

## Core Decision Tree

```
What is your data and purpose?

├── Compare sizes between categories → Bar Chart / Column Chart
├── Show trends over time → Line Chart / Area Chart
├── Display proportions of parts to the whole → Pie Chart / Ring Chart / Stacked Bar Chart
├── Show correlation between two variables → Scatter Plot / Bubble Chart
├── Display distribution patterns of data → Histogram / Box Plot / Violin Plot
└── Show relationship networks between nodes → G6 Graph (force/dagre/tree layout)
```

## Scenario One: Comparison

**Objective**: Compare the magnitude of values across different categories/time points.

| Data Characteristics | Recommended Chart | G2 Implementation |
|---------|---------|---------|
| Categories ≤ 10, vertical labels readable | **Bar Chart** | `type: 'interval'` |
| Long category names / Many categories | **Horizontal Bar Chart** | `type: 'interval'` + `coordinate: { transform: [{ type: 'transpose' }] }` |
| Multiple series side-by-side comparison | **Grouped Bar Chart** | `transform: [{ type: 'dodgeX' }]` |
| Show subclass contribution to total | **Stacked Bar Chart** | `transform: [{ type: 'stackY' }]` |

```javascript
// Bar Chart (most common comparison chart)
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'category' },
  transform: [{ type: 'sortX', by: 'y', reverse: true }],  // Sort by value in descending order
});
```

## Scenario Two: Trend

**Purpose**: Display the change of numerical values over time or sequence.

| Data Characteristics | Recommended Chart | G2 Implementation |
|---------|---------|---------|
| Single Metric Time Trend | **Line Chart** | `type: 'line'` |
| Multi-Metric Comparative Trend | **Multi-Series Line Chart** | `type: 'line'` + `encode.color: 'series'` |
| Emphasize Area/Cumulative Amount | **Area Chart** | `type: 'area'` |
| Show Quantity Increase/Decrease Over Time | **Stacked Area Chart** | `type: 'area'` + `transform: [{ type: 'stackY' }]` |

```javascript
// Multi-Series Line Chart
chart.options({
  type: 'line',
  data,
  encode: { x: 'date', y: 'value', color: 'series' },
  labels: [{ text: 'series', selector: 'last', position: 'right' }],
});
```

## Scenario Three: Part-to-Whole Ratio

**Objective**: Display the proportion of a part to the whole.

| Data Characteristics | Recommended Chart | G2 Implementation | Notes |
|---------|---------|---------|------|
| Categories ≤ 5, emphasis on proportion | **Pie Chart** | `interval` + `theta` coordinate | Difficult to distinguish between categories when there are many |
| Requires center whitespace | **Donut Chart** | Pie Chart + `innerRadius` | Can display total in the center |
| Many categories, emphasis on ranking | **Percentage Stacked Bar Chart** | `stackY` + `normalizeY` | |
| Multi-level proportions | **Sunburst Chart** | Temporarily use `sunburst` plugin | |

```javascript
// Pie Chart (Categories ≤ 5)
chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'category' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta', outerRadius: 0.85 },
  labels: [{
    text: (d) => `${d.category}\n${d.pct}%`,
    position: 'outside',
    connector: true,
  }],
});
```

## Scenario Four: Correlation

**Objective**: Explore the relationship between two or more variables

| Data Characteristics | Recommended Chart | G2 Implementation |
|---------|---------|---------|
| Two numerical variables | **Scatter Plot** | `type: 'point'` |
| Two numerical + third numerical dimension | **Bubble Chart** | `point` + `encode.size` |
| Multi-variable heat matrix | **Heatmap** | `type: 'cell'` |
| Show distribution + correlation | **Scatter Plot + Trend Line** | `view` + `point` + `line` |

```javascript
// Bubble Chart
chart.options({
  type: 'point',
  data,
  encode: {
    x: 'income',
    y: 'happiness',
    size: 'population',  // Third numerical dimension
    color: 'region',
  },
  scale: { size: { range: [4, 30] } },
});
```

## Scenario Five: Distribution

**Objective**: Understand the distribution pattern of data

| Data Feature | Recommended Chart | G2 Implementation |
|--------------||-------------------|-------------------|
| Single Variable Distribution | **Histogram** | `type: 'interval'` + `transform: [{ type: 'binX' }]` |
| Multi-group Distribution Comparison | **Box Plot** | `type: 'boxplot'` |
| Display Median/Quartiles | **Box Plot** | `type: 'boxplot'` |

```javascript
// Histogram
chart.options({
  type: 'interval',
  data,
  encode: { x: 'value', y: 'count' },
  transform: [{ type: 'binX', y: 'count' }],
});
```

## Scenario Six: Relationship Network

**Objective**: Display connections, hierarchical structures, and flows between entities.

| Data Characteristics | Recommended Library | G6 Layout |
|---------|--------|---------|
| Non-hierarchical network relationships | **G6** | `force` (Force-directed) |
| Directed processes/dependencies | **G6** | `dagre` (Directed Acyclic Graph) |
| Single-root tree hierarchy | **G6** | `compactBox` (Tree) |
| Peer-to-peer circular relationships | **G6** | `circular` (Circular) |

```javascript
// G6 Knowledge Graph (Force-directed)
const graph = new Graph({
  layout: { type: 'force', preventOverlap: true },
  data: { nodes, edges },
});
await graph.render();
```

## Quick Chart Selection Mnemonics

```
Compare with columns, trends with lines,
Proportions with pies, relationships with scatter,
Distributions with histograms, hierarchies with trees,
Networks with G6, complexity with combinations.
```

## Common Errors

### Error 1: Using Line Charts for Categorical Data Without Temporal Order

```javascript
// ❌ Misuse: City names have no inherent order, line charts imply a "trend" which is misleading
chart.options({
  type: 'line',
  data: [{ city: 'Beijing', gdp: 3.6 }, { city: 'Shanghai', gdp: 4.3 }],
  encode: { x: 'city', y: 'gdp' },   // ❌ Cities are unordered categories, not temporal data
});

// ✅ Correct: Use bar charts for categorical comparisons
chart.options({
  type: 'interval',
  data: [{ city: 'Beijing', gdp: 3.6 }, { city: 'Shanghai', gdp: 4.3 }],
  encode: { x: 'city', y: 'gdp' },
});
```

### Error 2: Using Pie Charts for 8+ Categories

```javascript
// ❌ Incorrect: Pie chart with 10 categories, sectors are hard to distinguish
chart.options({
  type: 'interval',
  coordinate: { type: 'theta' },
  // If there are 10 countries/regions... difficult to read
});

// ✅ Correct: Use sorted bar chart for more than 5 categories
chart.options({
  type: 'interval',
  encode: { x: 'country', y: 'value' },
  coordinate: { transform: [{ type: 'transpose' }] },
  transform: [{ type: 'sortX', by: 'y', reverse: true }],
});
```