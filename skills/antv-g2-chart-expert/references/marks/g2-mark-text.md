---
id: "g2-mark-text"
title: "G2 Text Mark"
description: |
  G2 v5 comes with a built-in text Mark for rendering custom text annotations in charts.
  The position is determined by `encode.x/y`, and the content is provided by `encode.text` or `style.text`.
  It is often used in conjunction with other Marks to achieve effects such as data labels, threshold annotations, and chart titles.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "text annotation"
  - "text"
  - "label"
  - "annotation"
  - "spec"

related:
  - "g2-mark-line-basic"
  - "g2-mark-interval-basic"
  - "g2-core-view-composition"
  - "g2-comp-annotation"

use_cases:
  - "Displaying value labels at the top of bar charts"
  - "Annotating special events or thresholds in charts"
  - "Adding custom chart titles or explanatory text"
  - "Highlighting text descriptions for specific data points"

difficulty: "beginner"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/annotation/annotation/#text"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  width: 600,
  height: 400,
});

const data = [
  { month: 'January', value: 120 },
  { month: 'February', value: 180 },
  { month: 'March', value: 150 },
  { month: 'April', value: 210 },
  { month: 'May', value: 170 },
];

chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'interval',
      encode: { x: 'month', y: 'value' },
    },
    {
      type: 'text',
      encode: {
        x: 'month',
        y: 'value',
        text: 'value',   // Data field name → Display the value of this field
      },
      style: {
        textAlign: 'center',
        dy: -8,           // Offset upwards
        fontSize: 12,
        fill: '#333',
      },
    },
  ],
});

chart.render();
```

## Fixed Position Text Annotation (Not Bound to Data)

```javascript
// Add a line of text at a fixed position on the chart (e.g., threshold description)
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'line',
      encode: { x: 'month', y: 'value' },
    },
    {
      // Fixed position text, using a single data point
      type: 'text',
      data: [{ x: 'March', y: 200, label: 'Threshold' }],
      encode: { x: 'x', y: 'y', text: 'label' },
      style: {
        fill: '#ff4d4f',
        fontSize: 12,
        fontWeight: 'bold',
        dx: 5,
      },
    },
  ],
});
```

## Combining lineY to Annotate Horizontal Threshold Lines

```javascript
// lineY + text combination: annotating threshold lines
chart.options({
  type: 'view',
  data,
  children: [
    {
      type: 'interval',
      encode: { x: 'month', y: 'value' },
      style: { fill: '#1890ff' },
    },
    {
      // Horizontal threshold line
      type: 'lineY',
      data: [{ y: 160 }],
      encode: { y: 'y' },
      style: { stroke: '#ff4d4f', lineDash: [4, 4], lineWidth: 1.5 },
    },
    {
      // Threshold annotation text
      type: 'text',
      data: [{ month: 'May', value: 160, label: 'Target 160' }],
      encode: { x: 'month', y: 'value', text: 'label' },
      style: {
        fill: '#ff4d4f',
        fontSize: 12,
        textAlign: 'right',
        dy: -6,
      },
    },
  ],
});
```

## Complete Configuration Options

```javascript
chart.options({
  type: 'text',
  data,
  encode: {
    x: 'xField',      // x position (corresponding to the axis field)
    y: 'yField',      // y position (corresponding to the axis field)
    text: 'textField', // displayed text content field
    color: 'series',  // color by series (optional)
  },
  style: {
    // Text style
    fontSize: 12,
    fontWeight: 'normal',
    fill: '#333',
    textAlign: 'center',    // 'left' | 'center' | 'right'
    textBaseline: 'bottom', // 'top' | 'middle' | 'bottom'

    // Position offset
    dx: 0,    // horizontal offset (px)
    dy: -8,   // vertical offset (px, negative value moves up)

    // Background box (optional)
    background: true,
    backgroundFill: 'rgba(255,255,255,0.8)',
    backgroundPadding: [2, 4],
    backgroundRadius: 3,

    // Rotation
    rotate: 0,   // rotation angle (degrees)
  },
});
```

## Scatter Plot Data Point Labels

```javascript
const scatterData = [
  { x: 10, y: 80, name: 'Product A' },
  { x: 20, y: 60, name: 'Product B' },
  { x: 35, y: 90, name: 'Product C' },
  { x: 50, y: 40, name: 'Product D' },
  { x: 65, y: 75, name: 'Product E' },
];

chart.options({
  type: 'view',
  data: scatterData,
  children: [
    {
      type: 'point',
      encode: { x: 'x', y: 'y' },
      style: { r: 6, fill: '#1890ff' },
    },
    {
      type: 'text',
      encode: { x: 'x', y: 'y', text: 'name' },
      style: {
        dy: -12,
        textAlign: 'center',
        fontSize: 11,
        fill: '#666',
      },
    },
  ],
});
```

## Common Errors and Fixes

### Error 1: Text Mark Used Independently Without Data

```javascript
// ❌ Incorrect: Text Mark requires data or inherits data from a parent view
chart.options({
  type: 'text',
  // Missing data, and no parent view provides data
  encode: { x: 'month', y: 'value', text: 'label' },
});

// ✅ Correct Approach 1: Provide data in the parent view
chart.options({
  type: 'view',
  data,               // Parent view provides data, child marks inherit automatically
  children: [
    { type: 'interval', encode: { x: 'month', y: 'value' } },
    { type: 'text', encode: { x: 'month', y: 'value', text: 'value' } },
  ],
});

// ✅ Correct Approach 2: Text Mark includes its own data (for fixed annotations)
chart.options({
  type: 'text',
  data: [{ x: 'March', y: 200, label: 'Special Annotation' }],
  encode: { x: 'x', y: 'y', text: 'label' },
});
```

### Error 2: `encode.text` is written as a literal string instead of a field name

```javascript
// ❌ Incorrect: `encode.text` should be a field name from the data, not a fixed string
chart.options({
  type: 'text',
  encode: {
    x: 'month',
    y: 'value',
    text: 'fixed text',   // ❌ This is a literal string, but there is no field named 'fixed text' in the data
  },
});

// ✅ Correct: Fixed text should be applied using `style.text` or a `transform` function
chart.options({
  type: 'text',
  encode: { x: 'month', y: 'value' },
  style: {
    text: (d) => `${d.value}`,   // ✅ Use a function to return the text content
    textAlign: 'center',
    dy: -8,
  },
});

// Alternatively, use a function in `encode`
chart.options({
  type: 'text',
  encode: {
    x: 'month',
    y: 'value',
    text: (d) => d.value,   // ✅ `encode.text` can be a function
  },
});
```
### Error 3: Forgetting to Share the View When Overlaying Text and Interval

```javascript
// ❌ Incorrect: Two independent charts cannot be overlaid
const chart1 = new Chart({ container: 'c1' });
chart1.options({ type: 'interval', data, encode: { x: 'month', y: 'value' } });

const chart2 = new Chart({ container: 'c2' });
chart2.options({ type: 'text', data, encode: { x: 'month', y: 'value', text: 'value' } });

// ✅ Correct: Overlay using view's children
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'interval', encode: { x: 'month', y: 'value' } },
    {
      type: 'text',
      encode: { x: 'month', y: 'value', text: 'value' },
      style: { textAlign: 'center', dy: -8 },
    },
  ],
});
```