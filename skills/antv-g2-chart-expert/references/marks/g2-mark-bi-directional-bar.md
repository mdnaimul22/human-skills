---
id: "g2-mark-bi-directional-bar"
title: "G2 Bi-Directional Bar Mark"
description: |
  Bi-directional bar mark. Uses the interval mark to display comparisons of positive and negative data.
  Suitable for scenarios such as positive/negative data comparison, income/expense comparison, completed/uncompleted comparison, etc.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "bi-directional bar chart"
  - "positive/negative bar chart"
  - "bi-directional"
  - "comparison"
  - "population pyramid"
  - "butterfly chart"
  - "symmetric bar chart"

related:
  - "g2-mark-interval-basic"
  - "g2-mark-interval-stacked"

use_cases:
  - "Positive/negative categorical data comparison"
  - "Income/expense comparison"
  - "Completed/uncompleted comparison"
  - "Population pyramid (male/female comparison)"
  - "Butterfly chart (left-right symmetric bar chart)"

anti_patterns:
  - "Not suitable for data without opposite meanings"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/bi-directional-bar"
---

## Core Concepts

The bidirectional bar chart displays comparisons of positive and negative data:
- Uses the `interval` mark
- Represents negative data through negative values
- Works with the `transpose` coordinate transformation

**Applicable Scenarios:**
- Completed/Uncompleted comparisons
- Revenue/Expenditure comparisons
- Positive/Negative data comparisons

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
});

const data = [
  { department: 'Department 1', people: 37, type: 'completed' },
  { department: 'Department 1', people: 9, type: 'uncompleted' },
  { department: 'Department 2', people: 27, type: 'completed' },
  { department: 'Department 2', people: 10, type: 'uncompleted' },
];

chart.options({
  type: 'interval',
  coordinate: { transform: [{ type: 'transpose' }] },
  data,
  encode: {
    x: 'department',
    y: (d) => (d.type === 'completed' ? d.people : -d.people),
    color: 'department',
  },
  style: {
    fill: ({ type }) => type === 'uncompleted' ? 'transparent' : undefined,
    stroke: ({ type }) => type === 'uncompleted' ? '#1890ff' : undefined,
    lineWidth: 2,
  },
});

chart.render();
```

## Common Variants

### Stacked Bidirectional Bar Chart

```javascript
chart.options({
  type: 'interval',
  coordinate: { transform: [{ type: 'transpose' }] },
  data,
  transform: [{ type: 'stackY' }],
  encode: {
    x: 'question',
    y: (d) =>
      d.type === 'Disagree' || d.type === 'Strongly disagree'
        ? -d.percentage
        : d.percentage,
    color: 'type',
  },
});
```

### Customizing Y-Axis Labels

```javascript
chart.options({
  type: 'interval',
  coordinate: { transform: [{ type: 'transpose' }] },
  data,
  encode: { x: 'category', y: (d) => d.type === 'A' ? d.value : -d.value },
  axis: {
    y: {
      labelFormatter: (d) => Math.abs(d),  // Display absolute values
    },
  },
});
```

### Group Display

```javascript
chart.options({
  type: 'interval',
  coordinate: { transform: [{ type: 'transpose' }] },
  data,
  encode: {
    x: 'group',
    y: (d) => d.direction === 'forward' ? d.value : -d.value,
    color: 'category',
  },
  style: {
    maxWidth: 20,
  },
});
```

## Complete Type Reference

```typescript
interface BiDirectionalData {
  category: string;      // Category field
  value: number;         // Numerical value
  direction: 'forward' | 'backward';  // Direction
}

interface BiDirectionalOptions {
  type: 'interval';
  coordinate: {
    transform: [{ type: 'transpose' }];
  };
  encode: {
    x: string;           // Category field
    y: (d) => number;    // Returns positive/negative value based on direction
    color?: string;
  };
}
```

## Bidirectional Bar Chart vs Bar Chart

| Feature | Bidirectional Bar Chart | Bar Chart |
|------|------------|--------|
| Data Direction | Positive and Negative Directions | Single Direction |
| Use Case | Comparing Opposite Meanings | Numerical Comparison |
| Visual Effect | Bidirectional Symmetry | Unidirectional |

## Population Pyramid (Butterfly Chart)

The population pyramid is a typical scenario of a bidirectional bar chart—data on the male and female sides are in opposite directions, achieved through negative value techniques, **without the need for `createView`**.

```javascript
const data = [
  { age: '0-4',   male: 5.3, female: 5.1 },
  { age: '5-9',   male: 5.6, female: 5.4 },
  { age: '10-14', male: 5.8, female: 5.5 },
  // ...
];

// Wide table to long table: Merge male/female into one column
const longData = data.flatMap((d) => [
  { age: d.age, sex: 'Male',   population: d.male },
  { age: d.age, sex: 'Female', population: d.female },
]);

chart.options({
  type: 'interval',
  data: longData,
  coordinate: { transform: [{ type: 'transpose' }] },  // Horizontal bar chart
  encode: {
    x: 'age',
    // Key: Use negative values for males and positive values for females → Create left-right symmetry
    y: (d) => d.sex === 'Male' ? -d.population : d.population,
    color: 'sex',
  },
  axis: {
    y: {
      labelFormatter: (d) => Math.abs(d),  // Display absolute values (no negative signs)
      title: 'Population Ratio (%)',
    },
    x: { title: 'Age Group' },
  },
  scale: {
    color: { range: ['#5B8FF9', '#FF7875'] },
  },
});
```

## Common Errors and Fixes

### Error 1: Missing Negative Value Conversion

```javascript
// ❌ Issue: All values are positive
encode: { y: 'value' }

// ✅ Correct: Return positive/negative values based on type
encode: { y: (d) => d.type === 'A' ? d.value : -d.value }
```

### Error 2: Missing transpose

```javascript
// ❌ Problem: Default is vertical direction
coordinate: {}

// ✅ Correct: Add transpose
coordinate: { transform: [{ type: 'transpose' }] }
```

### Error 3: Y-axis Labels Display Negative Values

```javascript
// ❌ Problem: Negative values are displayed as negative numbers
axis: {}

// ✅ Correct: Format as absolute values
axis: {
  y: { labelFormatter: (d) => Math.abs(d) },
}
```

### Error 4: Using `chart.createView()` to Implement a Population Pyramid

This is the most common mistake—in V4, `createView` was used to create two independent views on the left and right, but this API has been removed in V5. The correct approach is to use the **negative value technique** (single `interval` + negative value encoding) or `spaceLayer`.

```javascript
// ❌ Prohibited: V4 createView, does not exist in V5
const leftView = chart.createView();
leftView.options({
  type: 'interval',
  data: usData,
  encode: { x: 'age', y: 'male' },
});
const rightView = chart.createView();
rightView.options({ ... });

// ✅ Solution 1 (Recommended): Negative Value Technique—Single interval, males take negative values
chart.options({
  type: 'interval',
  data: combinedData,   // male/female merged into one array
  coordinate: { transform: [{ type: 'transpose' }] },
  encode: {
    x: 'age',
    y: (d) => d.sex === 'Male' ? -d.population : d.population,
    color: 'sex',
  },
  axis: { y: { labelFormatter: (d) => Math.abs(d) } },
});

// ✅ Solution 2: spaceLayer (use when both sides require completely independent scales)
chart.options({
  type: 'spaceLayer',
  children: [
    {
      type: 'interval',
      data: leftData,
      coordinate: { transform: [{ type: 'transpose' }, { type: 'reflectX' }] },
      encode: { x: 'age', y: 'male' },
      axis: { y: { position: 'right' } },
    },
    {
      type: 'interval',
      data: rightData,
      coordinate: { transform: [{ type: 'transpose' }] },
      encode: { x: 'age', y: 'female' },
      axis: { y: false },
    },
  ],
});
```