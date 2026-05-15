---
id: "g2-comp-geo-map"
title: "G2 Geo Map (geoView / geoPath / d3Projection)"
description: |
  G2 v5 implements geographic visualization through geoView, geoPath composite types, and d3Projection map projections.
  geoView is a geographic view container, and geoPath is a GeoJSON Mark (for drawing administrative regions, etc.).
  Supports multiple map projections such as geoMercator and geoNaturalEarth1.
  The data format is a GeoJSON FeatureCollection.

library: "g2"
version: "5.x"
category: "compositions"
tags:
  - "geoView"
  - "geoPath"
  - "map"
  - "GeoJSON"
  - "geographic visualization"
  - "d3Projection"
  - "choropleth"
  - "choropleth map"

related:
  - "g2-comp-geoview"
  - "g2-core-view-composition"

use_cases:
  - "Province/City distribution choropleth map"
  - "World map visualization"
  - "Spatial distribution display of geographic data"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/geo/geo/#choropleth"
---

## Core Concepts

The three core components of G2 geographic visualization:

| Component | Type | Description |
|------|------|------|
| `geoView` | composition | Geographic view container, configures projection and viewport |
| `geoPath` | mark (within geoView) | Renders GeoJSON geographic paths |
| `d3Projection` | projection function | Projection function exported from d3-geo (e.g., geoMercator) |

## Minimum Viable Example (World Map)

```javascript
import { Chart } from '@antv/g2';

async function renderMap() {
  // Load GeoJSON data
  const world = await fetch(
    'https://assets.antv.antgroup.com/g2/world.json',
  ).then((res) => res.json());

  const chart = new Chart({ container: 'container', width: 900, height: 500 });

  chart.options({
    type: 'geoView',       // Geo view container
    data: {
      type: 'fetch',
      value: 'https://assets.antv.antgroup.com/g2/world.json',
    },
    children: [
      {
        type: 'geoPath',   // Geo path Mark
        style: {
          fill: '#ccc',
          stroke: '#fff',
          lineWidth: 0.5,
        },
      },
    ],
  });

  chart.render();
}
renderMap();
```

## Choropleth Map

```javascript
import { Chart } from '@antv/g2';

const populationData = [
  { province: 'Guangdong', value: 12601 },
  { province: 'Shandong', value: 10169 },
  // ...
];

const chart = new Chart({ container: 'container', width: 900, height: 600 });

chart.options({
  type: 'geoView',
  children: [
    {
      type: 'geoPath',
      data: {
        type: 'fetch',
        value: 'https://assets.antv.antgroup.com/g2/china.json',
      },
      // Join GeoJSON properties with business data
      join: {
        populationData,
        on: ['properties.name', 'province'],   // GeoJSON property field → Business data field
      },
      encode: {
        color: 'value',   // Color by value field
      },
      style: {
        stroke: '#fff',
        lineWidth: 0.5,
      },
      scale: {
        color: {
          type: 'sequential',
          range: ['#eaf4d3', '#006d2c'],   // Color gradient range
        },
      },
    },
  ],
});

chart.render();
```

## Custom Map Projection

```javascript
import { Chart } from '@antv/g2';
import { geoMercator, geoNaturalEarth1 } from '@antv/g2';  // Import d3-geo projections from g2

const chart = new Chart({ container: 'container', width: 900, height: 500 });

chart.options({
  type: 'geoView',
  projection: {
    type: 'mercator',       // Built-in projection name
    // type: 'naturalEarth1', // Natural Earth projection
    // type: 'orthographic',  // Orthographic projection
  },
  children: [
    {
      type: 'geoPath',
      source: { type: 'fetch', value: 'https://assets.antv.antgroup.com/g2/world.json' },
      style: { fill: '#ccc', stroke: '#fff' },
    },
  ],
});

chart.render();
```

## Built-in Projection Types

```javascript
// G2 built-in d3-geo projections (specified in projection.type)
// 'mercator'         - Mercator projection (suitable for local areas)
// 'naturalEarth1'    - Natural Earth projection (suitable for world maps)
// 'orthographic'     - Orthographic projection (spherical effect)
// 'equalEarth'       - Equal Earth projection
// 'albersUsa'        - Albers USA projection
```

## Common Errors and Fixes

### Error: geoPath is not placed inside geoView
```javascript
// ❌ Error: geoPath must be used within geoView
chart.options({
  type: 'geoPath',   // ❌ Cannot be used directly as a top-level type
  geojson,
});

// ✅ Correct: geoPath is in geoView children
chart.options({
  type: 'geoView',
  children: [
    { type: 'geoPath', data: { type: 'fetch', value: '...' } },  // ✅
  ],
});
```

### Error: Data is not in GeoJSON format
```javascript
// ❌ Error: geoPath requires GeoJSON FeatureCollection format
chart.options({
  type: 'geoView',
  children: [{
    type: 'geoPath',
     [{ province: '广东', lng: 113, lat: 23 }],  // ❌ Regular latitude and longitude data is not acceptable
  }],
});

// ✅ Correct: Use standard GeoJSON FeatureCollection
// GeoJSON format: { type: 'FeatureCollection', features: [...] }
chart.options({
  type: 'geoView',
  children: [{
    type: 'geoPath',
     { type: 'fetch', value: 'china.geojson' },  // ✅ GeoJSON file
  }],
});
```