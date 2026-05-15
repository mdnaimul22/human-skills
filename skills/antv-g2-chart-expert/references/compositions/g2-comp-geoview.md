---
id: "g2-comp-geoview"
title: "G2 GeoView"
description: |
  geoView is based on D3 geo projection, enabling map visualization in G2.
  It supports various projection methods (mercator, equalEarth, orthographic, etc.),
  and requires data in GeoJSON format, rendering geographic shapes through the geoPath mark.

library: "g2"
version: "5.x"
category: "compositions"
tags:
  - "geoView"
  - "map"
  - "geography"
  - "GeoJSON"
  - "choropleth"
  - "geo projection"
  - "composition"

related:
  - "g2-mark-cell-heatmap"
  - "g2-scale-threshold"

use_cases:
  - "World choropleth map"
  - "Country/province data map display"
  - "Geospatial data visualization"

difficulty: "advanced"
completeness: "full"
created: "2025-03-24"
updated: "2025-03-24"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/examples/geo/geo/#choropleth"
---

## Minimum Viable Example (World Map)

```javascript
import { Chart } from '@antv/g2';

// Need to load world.geo.json data in advance
fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')
  .then(res => res.json())
  .then(world => {
    // Convert TopoJSON to GeoJSON (requires topojson-client)
    const countries = topojson.feature(world, world.objects.countries);

    const chart = new Chart({ container: 'container', width: 900, height: 500 });

    chart.options({
      type: 'geoView',
      coordinate: {
        type: 'projection',
        projection: 'equalEarth',   // Projection method
      },
      children: [
        {
          type: 'geoPath',
          data: countries,
          encode: { color: 'id' },   // Color by country id
          style: {
            stroke: '#fff',
            lineWidth: 0.5,
            fillOpacity: 0.85,
          },
        },
      ],
    });

    chart.render();
  });
```

## Choropleth (Data-Driven Coloring)

```javascript
// Associate GeoJSON with a data table by 'name' to achieve data-driven coloring
const gdpData = {
  CN: 17.7, US: 25.5, JP: 4.2, DE: 4.1,
  // ...
};

chart.options({
  type: 'geoView',
  coordinate: { type: 'projection', projection: 'mercator' },
  children: [
    {
      type: 'geoPath',
      geoJsonFeatures,
      encode: {
        color: (d) => gdpData[d.properties.iso_a2] || 0,  // Associate with GDP data
      },
      scale: {
        color: {
          type: 'sequential',
          palette: 'blues',
          unknown: '#eee',   // Color for countries with no data
        },
      },
      tooltip: {
        items: [
          { field: 'properties.name', name: 'Country' },
          { callback: (d) => gdpData[d.properties.iso_a2], name: 'GDP (Trillions USD)' },
        ],
      },
    },
  ],
});
```

## Supported Projection Methods

```javascript
// Common Projections
coordinate: { type: 'projection', projection: 'mercator' }       // Mercator (Web Map Standard)
coordinate: { type: 'projection', projection: 'equalEarth' }     // Equal Earth
coordinate: { type: 'projection', projection: 'orthographic' }   // Orthographic (Spherical)
coordinate: { type: 'projection', projection: 'naturalEarth1' }  // Natural Earth
coordinate: { type: 'projection', projection: 'albersUsa' }      // Albers USA
```

## Common Errors and Fixes

### Error: Data is not in GeoJSON format—Directly using traditional data
```javascript
// ❌ geoPath mark requires GeoJSON Feature/FeatureCollection data
chart.options({
  children: [{
    type: 'geoPath',
    [{ country: 'China', gdp: 17.7 }],  // ❌ Not GeoJSON
  }],
});

// ✅ Requires GeoJSON format
chart.options({
  children: [{
    type: 'geoPath',
    { type: 'FeatureCollection', features: [...] },  // ✅ GeoJSON
  }],
});
```