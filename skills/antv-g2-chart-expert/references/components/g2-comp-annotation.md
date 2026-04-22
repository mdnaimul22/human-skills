---
id: "g2-comp-annotation"
title: "G2 Annotation"
description: |
  In G2 v5, annotations are implemented by overlaying additional Marks (text, line, image, etc.) on the chart.
  Common types include text annotations, reference lines, and reference areas.
  This article uses the Spec mode's view + children approach to combine annotations.

library: "g2"
version: "5.x"
category: "components"
tags:
  - "annotation"
  - "标注"
  - "参考线"
  - "reference line"
  - "文字标注"
  - "lineX"
  - "lineY"
  - "spec"

related:
  - "g2-core-view-composition"
  - "g2-comp-axis-config"

use_cases:
  - "Add average lines, target lines to charts"
  - "Annotate special data points (max, min)"
  - "Add reference area background color"

difficulty: "intermediate"
completeness: "full"
created: "2024-01-01"
updated: "2025-03-01"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/extra-topics/annotation"
---
## Horizontal Reference Line (lineY)

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'view',
  data,
  children: [
    // Main chart: Line chart
    {
      type: 'line',
      encode: { x: 'month', y: 'value' },
    },
    // Annotation: Horizontal reference line at y=60
    {
      type: 'lineY',
      data: [60],
      style: {
        stroke: '#f5222d',
        strokeDasharray: '4 4',
        lineWidth: 1.5,
      },
      labels: [
        {
          text: 'Target value: 60',
          position: 'right',
          style: { fill: '#f5222d', fontSize: 11 },
        },
      ],
    },
  ],
});

chart.render();
```

## Vertical Reference Line (lineX)

```javascript
// Mark a specific time point
{
  type: 'lineX',
  data: [new Date('2024-03-01')],
  style: { stroke: '#722ed1', strokeDasharray: '4 4', lineWidth: 1.5 },
  labels: [
    { text: 'Version Release', position: 'top', style: { fill: '#722ed1' } },
  ],
}
```

## Annotate Maximum Value Point

```javascript
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'line', encode: { x: 'month', y: 'value' } },
    {
      // Use point + text to annotate the maximum value
      type: 'point',
      data,
      encode: { x: 'month', y: 'value' },
      transform: [{ type: 'select', channel: 'y', selector: 'max' }],  // Select only the maximum value point
      style: { fill: '#f5222d', r: 5 },
      labels: [
        {
          text: (d) => `Maximum\n${d.value}`,
          position: 'top',
          style: { fill: '#f5222d', fontSize: 11 },
        },
      ],
    },
  ],
});
```

## Reference Range (rangeX / rangeY)

```javascript
// Highlight a specific y-value range (e.g., normal range)
{
  type: 'rangeY',
  data: [{ y: [40, 80] }],
  style: {
    fill: '#52c41a',
    fillOpacity: 0.08,
  },
  labels: [
    {
      text: 'Normal Range',
      position: 'right',
      style: { fill: '#52c41a', fontSize: 11 },
    },
  ],
}
```

## Text Mark (text mark)

```javascript
// Add text at specified coordinates
{
  type: 'text',
  data: [{ x: 'Mar', y: 91, label: 'Highest point' }],
  encode: { x: 'x', y: 'y', text: 'label' },
  style: {
    textAlign: 'center',
    textBaseline: 'bottom',
    fill: '#1890ff',
    fontSize: 12,
    dy: -6,
  },
}
```

## Image Mark (image mark)

```javascript
// Add an image mark at the center of the chart
{
  type: 'image',
  data: [{
    src: 'https://gw.alipayobjects.com/zos/rmsportal/KDpgvguMpGfqaHPjicRK.svg',
    x: '50%',
    y: '50%'
  }],
  encode: { 
    x: 'x', 
    y: 'y', 
    src: 'src' 
  },
  style: {
    width: 80,
    height: 80,
    textAlign: 'center',
    textBaseline: 'middle'
  }
}
```

## Common Errors and Fixes

### Error: Directly Overlaying Annotations in a Non-View Container
```javascript
// ❌ Incorrect: Multiple chart.options() will overwrite each other
chart.options({ type: 'line', ... });
chart.options({ type: 'lineY', ... });  // Overwrites the line chart!

// ✅ Correct: Use type: 'view' + children array to overlay
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'line', ... },
    { type: 'lineY', ... },
  ],
});
```

### Error: Incorrect Position and Encoding of Image Annotations
```javascript
// ❌ Error: Using a function to return fixed coordinates, not bound to data channels
{
  type: 'image',
  data: [{ url: 'https://example.com/image.png' }],
  encode: {
    x: () => 0, // Fixed at center
    y: () => 0  // Fixed at center
  },
  style: {
    img: (d) => d.url,
    width: 80,
    height: 80
  }
}

// ✅ Correct: Using relative percentage coordinates and correctly mapping the src channel
{
  type: 'image',
  data: [{
    src: 'https://example.com/image.png',
    x: '50%',
    y: '50%'
  }],
  encode: { 
    x: 'x', 
    y: 'y', 
    src: 'src' 
  },
  style: {
    width: 80,
    height: 80
  }
}
```