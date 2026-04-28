---
id: "g2-mark-rangex"
title: "G2 RangeX / RangeY Range Annotation"
description: |
  rangeX draws vertical bands (range highlights) along the X-axis, commonly used to annotate specific time periods or threshold ranges.
  rangeY draws horizontal bands along the Y-axis, used to annotate a specific numerical range (e.g., target range, warning line).
  Often combined with line charts to add time range annotations in the background.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "rangeX"
  - "rangeY"
  - "range"
  - "annotation"
  - "highlight area"
  - "reference area"
  - "time range"

related:
  - "g2-comp-annotation"
  - "g2-mark-line-basic"
  - "g2-comp-view"

use_cases:
  - "Highlighting special time periods in time series charts (e.g., historical events, holidays)"
  - "Annotating normal value ranges (e.g., green safety range)"
  - "Highlighting a specific data range"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/annotation/range/"
---

## Minimum Viable Example (Time Period Highlighting)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 800, height: 400 });

chart.options({
  type: 'view',
  children: [
    // Main Line Chart
    {
      type: 'line',
      data: [
        { date: '2024-01', value: 100 },
        { date: '2024-02', value: 120 },
        { date: '2024-03', value: 150 },
        { date: '2024-04', value: 130 },
        { date: '2024-05', value: 160 },
      ],
      encode: { x: 'date', y: 'value' },
      style: { lineWidth: 2 },
    },
    // Highlight Special Area
    {
      type: 'rangeX',
      data: [
        { x: '2024-02', x1: '2024-03', label: 'Event Period' },
      ],
      encode: { x: 'x', x1: 'x1' },
      style: { fill: '#FF6B35', fillOpacity: 0.15 },
      labels: [{ text: 'label', position: 'top', style: { fontSize: 11 } }],
    },
  ],
});

chart.render();
```

## Time Interval Annotation (Line Chart + Historical Event Background)

Using Date objects and array format to annotate historical time periods:

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  autoFit: true,
});

// Population data
const populationData = [
  { year: '1875', population: 1309 },
  { year: '1890', population: 1558 },
  { year: '1910', population: 4512 },
  { year: '1925', population: 8180 },
  { year: '1933', population: 15915 },
  { year: '1939', population: 24824 },
  { year: '1946', population: 28275 },
  { year: '1950', population: 29189 },
  { year: '1964', population: 29881 },
  { year: '1971', population: 26007 },
];

chart.options({
  type: 'view',
  autoFit: true,
  children: [
    // Background interval annotation (historical periods)
    {
      type: 'rangeX',
      data: [
        { year: [new Date('1933'), new Date('1945')], event: 'Nazi Rule Period' },
        { year: [new Date('1948'), new Date('1989')], event: 'East Germany Period' },
      ],
      encode: { x: 'year', color: 'event' },
      scale: {
        color: {
          independent: true,  // Independent color scale, different color for each interval
          range: ['#FAAD14', '#30BF78'],
        },
      },
      style: { fillOpacity: 0.75 },
      tooltip: false,
    },
    // Line chart
    {
      type: 'line',
      data: populationData,
      encode: {
        x: (d) => new Date(d.year),
        y: 'population',
      },
      style: { stroke: '#333', lineWidth: 2 },
    },
    // Data points
    {
      type: 'point',
      data: populationData,
      encode: {
        x: (d) => new Date(d.year),
        y: 'population',
      },
      style: { fill: '#333', r: 3 },
    },
  ],
});

chart.render();
```

## Data Format Description

rangeX supports two data formats:

### Format 1: Separate Fields (x, x1)

```javascript
[
  { x: '2024-01', x1: '2024-03', label: 'Q1' },
  { x: '2024-04', x1: '2024-06', label: 'Q2' },
],
encode: { x: 'x', x1: 'x1' },
```

### Format 2: Array Field

```javascript
data: [
  { year: [new Date('1933'), new Date('1945')], event: 'Event A' },
  { year: [new Date('1948'), new Date('1989')], event: 'Event B' },
],
encode: { x: 'year' },  // Array is automatically parsed as [start, end]
```

## RangeY (Horizontal Reference Range)

```javascript
chart.options({
  type: 'view',
  children: [
    {
      type: 'line',
      data,
      encode: { x: 'date', y: 'temperature' },
    },
    // Mark the normal temperature range (18~26°C)
    {
      type: 'rangeY',
      data: [{ y: 18, y1: 26, label: 'Comfortable Range' }],
      encode: { y: 'y', y1: 'y1' },
      style: { fill: '#52c41a', fillOpacity: 0.1 },
      labels: [{ text: 'label', position: 'right', style: { fill: '#52c41a' } }],
    },
  ],
});
```

## Configuration Options

| Property | Description | Type |
|------|------|------|
| `encode.x` | Start field of the interval | `string \| (d) => value` |
| `encode.x1` | End field of the interval | `string \| (d) => value` |
| `encode.color` | Color field (distinguishes different intervals) | `string` |
| `style.fill` | Fill color | `string` |
| `style.fillOpacity` | Fill opacity | `number` (0-1) |
| `scale.color.independent` | Independent color scale | `boolean` |

## Common Errors and Fixes

### Error 1: Writing x/x1 as an array instead of independent field names in encode

```javascript
// ❌ Incorrect: x and x1 in rangeX are independent fields, not an array
chart.options({
  type: 'rangeX',
  encode: { x: ['start', 'end'] },  // ❌ Incorrect usage
});

// ✅ Correct: x and x1 are bound to start and end fields respectively
chart.options({
  type: 'rangeX',
  data: [{ start: '2024-01', end: '2024-03' }],
  encode: {
    x: 'start',    // ✅ Start field
    x1: 'end',     // ✅ End field
  },
});
```

### Error 2: Inconsistent Time Formats Causing Range Misalignment with the Main Chart

```javascript
// ❌ Incorrect: Line chart uses Date object, rangeX uses string, inconsistent scales
children: [
  { type: 'line', encode: { x: (d) => new Date(d.year) } },
  { type: 'rangeX', encode: { x: 'year' } },  // ❌ Inconsistent format
]

// ✅ Correct: Uniform use of Date objects
children: [
  { type: 'line', encode: { x: (d) => new Date(d.year) } },
  { type: 'rangeX', encode: { x: 'year' }, data: [
    { year: [new Date('1933'), new Date('1945')] }  // ✅ Also uses Date
  ]},
]
```

### Error 3: Multiple Intervals with the Same Color

```javascript
// ❌ Issue: Multiple intervals default to using a continuous color palette, resulting in similar colors
{
  type: 'rangeX',
  data: [
    { year: [start1, end1], event: '事件A' },
    { year: [start2, end2], event: '事件B' },
  ],
  encode: { x: 'year', color: 'event' },
}

// ✅ Correct: Use independent: true to color each interval independently
{
  type: 'rangeX',
  data: [
    { year: [start1, end1], event: '事件A' },
    { year: [start2, end2], event: '事件B' },
  ],
  encode: { x: 'year', color: 'event' },
  scale: {
    color: {
      independent: true,  // ✅ Independent colors
      range: ['#FAAD14', '#30BF78'],
    },
  },
}
```
### Error 4: Placing rangeX behind the line chart causes occlusion

```javascript
// ❌ Incorrect: rangeX placed later, occludes the line
children: [
  { type: 'line', ... },
  { type: 'rangeX', ... },  // ❌ Occludes the line
]

// ✅ Correct: Place rangeX first as the background layer
children: [
  { type: 'rangeX', ... },  // ✅ Rendered first, acts as background
  { type: 'line', ... },
]
```