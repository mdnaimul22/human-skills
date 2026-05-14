---
id: "g2-mark-wordcloud"
title: "G2 Word Cloud (wordCloud)"
description: |
  The wordCloud mark arranges words into a cloud-like layout based on their frequency/weight, with higher frequency words displayed in larger fonts.
  The data must include a text field (text) and a weight field (value).
  G2 has a built-in word cloud layout algorithm that automatically handles word overlapping.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "word cloud"
  - "wordCloud"
  - "text visualization"
  - "word frequency"

related:
  - "g2-mark-text"
  - "g2-core-chart-init"

use_cases:
  - "Displaying word frequency distribution in text data"
  - "Visualizing key terms from user comments"
  - "Showcasing topic popularity"

difficulty: "intermediate"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/general/other/#word-cloud"
---

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const data = [
  { word: 'Data Visualization', count: 120 },
  { word: 'Chart', count: 85 },
  { word: 'Interaction', count: 70 },
  { word: 'JavaScript', count: 95 },
  { word: 'Frontend', count: 110 },
  { word: 'AntV', count: 65 },
  { word: 'G2', count: 100 },
  { word: 'Analysis', count: 78 },
  { word: 'User', count: 55 },
  { word: 'Experience', count: 60 },
];

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'wordCloud',
  data,
  encode: {
    text: 'word',    // Displayed word field
    color: 'word',   // Color encoding (different color for each word)
    fontSize: {      // Font size mapping (can use field name or fixed range)
      field: 'count',
      range: [12, 60],  // Minimum/maximum font size
    },
  },
  layout: {
    spiral: 'archimedean',  // Layout spiral shape: 'archimedean' | 'rectangular'
    padding: 2,             // Word spacing
  },
  style: {
    fontFamily: 'Impact, sans-serif',
    fontWeight: 'bold',
  },
});

chart.render();
```

## Word Cloud with Rotation

```javascript
chart.options({
  type: 'wordCloud',
  data,
  encode: {
    text: 'word',
    color: 'count',
    rotate: {
      // Random rotation angle: horizontal or vertical
      callback: () => (Math.random() > 0.7 ? 90 : 0),
    },
    fontSize: { field: 'count', range: [14, 56] },
  },
  scale: {
    color: { type: 'sequential', palette: 'blues' },
  },
  layout: { padding: 4 },
});
```

## Fixed Phrase Color Grouping

```javascript
chart.options({
  type: 'wordCloud',
  data: wordsWithCategory,
  encode: {
    text: 'word',
    color: 'category',  // Color by category (categorical palette)
    fontSize: { field: 'count', range: [16, 50] },
  },
  scale: {
    color: { type: 'ordinal', palette: 'set2' },
  },
});
```

## Common Errors and Fixes

### Error 1: Data Lacks Weight Field—All Words Are the Same Size
```javascript
// ❌ No fontSize encoding, all words are the same size
chart.options({
  type: 'wordCloud',
  data: [{ word: 'A' }, { word: 'B' }],  // ❌ No numerical field
  encode: { text: 'word' },
});

// ✅ Must provide a weight field and configure fontSize
chart.options({
  encode: {
    text: 'word',
    fontSize: { field: 'count', range: [14, 60] },  // ✅
  },
});
```

### Error 2: Container Too Small Causes Truncated Words
```javascript
// ❌ Word cloud layout algorithm cannot place all words in a small container
const chart = new Chart({ container: 'container', width: 300, height: 200 });  // ❌ Too small

// ✅ Word cloud recommends a minimum of 400×300, and 600×400 or larger for many words
const chart = new Chart({ container: 'container', width: 640, height: 480 });  // ✅
```

### Error 3: Too Many Words with Excessively Large Font Size—Many Words Cannot Be Laid Out
```javascript
// ❌ 100+ words, maximum font size 80px, many words are discarded
encode: { fontSize: { field: 'count', range: [20, 80] } }  // ❌ range is too large

// ✅ Reduce font size range when there are many words
encode: { fontSize: { field: 'count', range: [10, 40] } }  // ✅
```