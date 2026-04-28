---
id: "g2-data-transform-patterns"
title: "G2 Data Transformation Patterns"
description: |
  The most commonly used data preprocessing patterns before G2 visualization: wide-to-long (fold), group aggregation,
  percentage calculation, ranking/sorting, data filtering, and time granularity aggregation.
  These patterns can be completed either in JavaScript frontend or using G2's built-in data transform.

library: "g2"
version: "5.x"
category: "data"
tags:
  - "data transformation"
  - "data processing"
  - "wide-to-long"
  - "fold"
  - "group aggregation"
  - "percentage"
  - "sorting"
  - "time aggregation"

related:
  - "g2-data-fold"
  - "g2-data-filter"
  - "g2-data-sort"
  - "g2-data-slice"

use_cases:
  - "Convert wide table returned by API to long table required by G2"
  - "Perform aggregation, ranking, and percentage calculation on data in the frontend"
  - "Prepare data in corresponding formats for different chart types"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-27"
author: "antv-team"
---

## Core Concepts

**There are two ways to transform data**:

1. **JavaScript Frontend Preprocessing**: Process data using JS functions before passing it to G2.
2. **G2 Built-in Data Transform**: Configured in `data.transform`, declarative processing.

**Recommendation**: Prioritize using G2's built-in transform for more concise and serializable code.

## Pattern 1: Wide to Long Table Transformation

**Scenario**: The backend returns a wide table with one metric per column, which needs to be transformed into a long table with one observation per row.

**JavaScript Method**:
```javascript
// Input: Wide table
const wideData = [
  { month: 'Jan', 北京: 3.6, 上海: 4.3, 广州: 2.8 },
  { month: 'Feb', 北京: 3.8, 上海: 4.5, 广州: 3.0 },
];

function wideToLong(data, idCols, valueCols, keyName = 'key', valueName = 'value') {
  return data.flatMap(row =>
    valueCols.map(col => ({
      ...Object.fromEntries(idCols.map(id => [id, row[id]])),
      [keyName]: col,
      [valueName]: row[col],
    }))
  );
}

const longData = wideToLong(wideData, ['month'], ['北京', '上海', '广州'], 'city', 'gdp');
// Output:
// [
//   { month: 'Jan', city: '北京', gdp: 3.6 },
//   { month: 'Jan', city: '上海', gdp: 4.3 },
//   ...
// ]
```

**G2 Built-in Solution** (Recommended):
```javascript
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: wideData,
    transform: [{
      type: 'fold',
      fields: ['北京', '上海', '广州'],
      key: 'city',
      value: 'gdp',
    }],
  },
  encode: { x: 'month', y: 'gdp', color: 'city' },
});
```

## Pattern 2: Group + Aggregate

**Scenario**: Group by a field and calculate the sum/mean/count of another field.

**JavaScript Approach**:
```javascript
// Input: Detailed data
const orderData = [
  { month: 'Jan', region: 'East China', amount: 1200 },
  { month: 'Jan', region: 'East China', amount: 800 },
  { month: 'Jan', region: 'South China', amount: 950 },
  { month: 'Feb', region: 'East China', amount: 1500 },
];

function groupSum(data, groupKeys, sumKey) {
  const map = new Map();
  data.forEach(row => {
    const key = groupKeys.map(k => row[k]).join('|');
    if (!map.has(key)) {
      const group = Object.fromEntries(groupKeys.map(k => [k, row[k]]));
      group[sumKey] = 0;
      map.set(key, group);
    }
    map.get(key)[sumKey] += row[sumKey];
  });
  return Array.from(map.values());
}

const aggregated = groupSum(orderData, ['month', 'region'], 'amount');
// Output:
// [
//   { month: 'Jan', region: 'East China', amount: 2000 },
//   { month: 'Jan', region: 'South China', amount: 950 },
//   { month: 'Feb', region: 'East China', amount: 1500 },
// ]
```

**G2 Built-in Solution** (using mark transform):
```javascript
chart.options({
  type: 'interval',
  data: orderData,
  encode: { x: 'month', y: 'amount', color: 'region' },
  transform: [{ type: 'groupX', y: 'sum' }],  // Group by x and calculate sum
});
```

## Pattern 3: Percentage Calculation

**Scenario**: Calculate the percentage of each category relative to the total (pie chart labels, percentage bar chart)

**JavaScript Approach**:
```javascript
function addPercentage(data, valueKey, pctKey = 'pct') {
  const total = data.reduce((sum, d) => sum + (d[valueKey] || 0), 0);
  return data.map(d => ({
    ...d,
    [pctKey]: total > 0 ? ((d[valueKey] / total) * 100).toFixed(1) : '0.0',
  }));
}

const dataWithPct = addPercentage(
  [{ city: 'Beijing', gdp: 3.6 }, { city: 'Shanghai', gdp: 4.3 }, { city: 'Guangzhou', gdp: 2.8 }],
  'gdp'
);
// Output: [{ city: 'Beijing', gdp: 3.6, pct: '33.6' }, ...]
```

**G2 Built-in Solution** (Percentage Bar Chart):
```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'city', y: 'gdp', color: 'city' },
  transform: [{ type: 'normalizeY' }],  // Normalize Y-axis to percentage
});
```

**Using Percentage in Pie Chart Labels**:
```javascript
const total = data.reduce((sum, d) => sum + d.value, 0);

chart.options({
  type: 'interval',
  data,
  encode: { y: 'value', color: 'type' },
  transform: [{ type: 'stackY' }],
  coordinate: { type: 'theta' },
  labels: [{
    text: (d) => `${d.type}\n${((d.value / total) * 100).toFixed(1)}%`,
    position: 'outside',
  }],
});
```

## Pattern 4: Ranking / Top N

**Scenario**: Retrieve the top/bottom N data points by value, used for ranking charts

**JavaScript Approach**:
```javascript
function topN(data, valueKey, n, ascending = false) {
  return [...data]
    .sort((a, b) => ascending ? a[valueKey] - b[valueKey] : b[valueKey] - a[valueKey])
    .slice(0, n);
}

const top5Cities = topN(cityData, 'gdp', 5);
```

**G2 Built-in Solution**:
```javascript
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: cityData,
    transform: [
      { type: 'sortBy', fields: [['gdp', false]] },  // Sort by gdp in descending order
      { type: 'slice', end: 5 },                      // Take only the top 5
    ],
  },
  encode: { x: 'city', y: 'gdp' },
});
```

## Pattern 5: Time Granularity Aggregation

**Scenario**: Daily granularity data aggregated into weekly/monthly/quarterly

**JavaScript Approach**:
```javascript
// Daily granularity → Monthly granularity aggregation
function aggregateByMonth(data, dateKey, valueKey) {
  const map = new Map();
  data.forEach(d => {
    const date = new Date(d[dateKey]);
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    if (!map.has(monthKey)) {
      map.set(monthKey, { month: monthKey, total: 0, count: 0 });
    }
    const entry = map.get(monthKey);
    entry.total += d[valueKey];
    entry.count += 1;
  });
  return Array.from(map.values())
    .map(({ month, total, count }) => ({
      month,
      value: total,
      avg: total / count,
    }))
    .sort((a, b) => a.month.localeCompare(b.month));
}

// Monthly granularity → Quarterly granularity
function aggregateByQuarter(data, monthKey, valueKey) {
  return data.reduce((acc, d) => {
    const [year, month] = d[monthKey].split('-');
    const quarter = `${year}-Q${Math.ceil(Number(month) / 3)}`;
    const existing = acc.find(a => a.quarter === quarter);
    if (existing) {
      existing[valueKey] += d[valueKey];
    } else {
      acc.push({ quarter, [valueKey]: d[valueKey] });
    }
    return acc;
  }, []);
}
```

## Pattern 6: Data Filtering and Conditional Selection

**Scenario**: Filter data based on dimensions/time ranges

**JavaScript Approach**:
```javascript
function filterData(data, conditions) {
  return data.filter(d =>
    conditions.every(({ key, op, value }) => {
      switch (op) {
        case 'eq':  return d[key] === value;
        case 'gt':  return d[key] > value;
        case 'lt':  return d[key] < value;
        case 'gte': return d[key] >= value;
        case 'lte': return d[key] <= value;
        case 'in':  return value.includes(d[key]);
        default:    return true;
      }
    })
  );
}

const filtered = filterData(data, [
  { key: 'region', op: 'in',  value: ['East China', 'South China'] },
  { key: 'sales',  op: 'gt',  value: 1000 },
]);
```

**G2 Built-in Solution**:
```javascript
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: data,
    transform: [
      { type: 'filter', callback: (d) => ['East China', 'South China'].includes(d.region) && d.sales > 1000 },
    ],
  },
  encode: { x: 'region', y: 'sales' },
});
```

**Interactive Filtering Example**:
```javascript
document.getElementById('region-select').addEventListener('change', (e) => {
  const region = e.target.value;
  const filtered = region === 'all'
    ? allData
    : allData.filter(d => d.region === region);
  chart.changeData(filtered);
});
```

## Pattern 7: Data Normalization (0-1 Standardization)

**Scenario**: When comparing multiple metrics, normalize data of different scales to the same range.

**JavaScript Approach**:
```javascript
// Min-Max Normalization
function normalize(data, valueKey, normalizedKey = 'normalized') {
  const values = data.map(d => d[valueKey]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  return data.map(d => ({
    ...d,
    [normalizedKey]: (d[valueKey] - min) / range,
  }));
}

// Normalize Multiple Metrics Separately (Preparation for Radar Chart/Parallel Coordinates)
function normalizeMultiple(data, keys) {
  return keys.reduce((acc, key) => normalize(acc, key, `${key}_norm`), data);
}
```

## Common Errors and Fixes

### Error 1: Field names after fold do not match encode

```javascript
// ❌ fold is configured with key='city', value='gdp', but encode still uses the original field names
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: wideData,
    transform: [{ type: 'fold', fields: ['北京', '上海'], key: 'city', value: 'gdp' }],
  },
  encode: { color: '北京' },  // ❌ The '北京' field has been eliminated by fold
});

// ✅ encode should use the new field names generated by fold
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: wideData,
    transform: [{ type: 'fold', fields: ['北京', '上海'], key: 'city', value: 'gdp' }],
  },
  encode: { y: 'gdp', color: 'city' },  // ✅ Use the field names configured by key/value
});
```

### Error 2: Confusion between data transform and mark transform

```javascript
// ❌ Incorrect: fold is a data transformation and should not be placed in mark transform
chart.options({
  type: 'interval',
  wideData,
  transform: [{ type: 'fold', fields: ['北京', '上海'] }],  // ❌ Incorrect position
});

// ✅ Correct: fold is placed in data.transform
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: wideData,
    transform: [{ type: 'fold', fields: ['北京', '上海'], key: 'city', value: 'gdp' }],
  },
  transform: [{ type: 'stackY' }],  // mark transform
});
```