---
id: "g2-pattern-responsive"
title: "G2 Responsive Chart Adaptation"
description: |
  Automatically adjust chart width, height, font size, margins, and other configurations based on different screen sizes and container dimensions.
  Covers autoFit configuration, dynamic adjustments using ResizeObserver, and common issues in mobile adaptation.

library: "g2"
version: "5.x"
category: "patterns"
tags:
  - "responsive"
  - "autoFit"
  - "resize"
  - "mobile"
  - "container size"

related:
  - "g2-core-chart-init"

use_cases:
  - "Automatically adjust charts based on browser window/container size changes"
  - "Share the same chart component between mobile and desktop"
  - "Embed in dynamically sized containers like popups/sidebars"

difficulty: "intermediate"
completeness: "full"
---
## G2 Adaptive Width (autoFit)

```javascript
import { Chart } from '@antv/g2';

// Option 1: autoFit: true (Width automatically adapts to the container, height is fixed)
const chart = new Chart({
  container: 'container',
  autoFit: true,     // Width = container width, height uses default value
  height: 400,       // Height is fixed
});

chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value' },
});

chart.render();
```

## ResizeObserver Dynamically Responds to Container Changes

```javascript
// Solution 2: Listen for container size changes and manually adjust the chart
const container = document.getElementById('container');
const chart = new Chart({
  container: 'container',
  width: container.clientWidth,
  height: container.clientHeight,
});

chart.options({ type: 'interval', data, encode: { x: 'month', y: 'value' } });
chart.render();

// Listen for container size changes
const resizeObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    const { width, height } = entry.contentRect;
    chart.changeSize(width, height);
 }
});
resizeObserver.observe(container);

// Clean up when the page unloads
window.addEventListener('unload', () => {
  resizeObserver.disconnect();
  chart.destroy();
});
```

## Window Resize Event (Simple Solution)

```javascript
// Solution 3: Listen for window resize (debounce handling)
function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

const handleResize = debounce(() => {
  const container = document.getElementById('container');
  chart.changeSize(container.clientWidth, container.clientHeight);
}, 300);

window.addEventListener('resize', handleResize);
```

## Responsive Chart Font/Margin Adaptation

```javascript
// Dynamically adjust font size and margin based on container width
function getResponsiveConfig(containerWidth) {
  const isMobile = containerWidth < 480;
  const isTablet = containerWidth < 768;

  return {
    fontSize: isMobile ? 10 : isTablet ? 11 : 12,
    tickCount: isMobile ? 4 : isTablet ? 6 : 10,
    labelRotate: isMobile ? Math.PI / 4 : 0,   // Rotate labels on mobile
    marginBottom: isMobile ? 40 : 20,
  };
}

const containerWidth = document.getElementById('container').clientWidth;
const config = getResponsiveConfig(containerWidth);

chart.options({
  type: 'interval',
  data,
  encode: { x: 'month', y: 'value' },
  axis: {
    x: {
      labelFontSize: config.fontSize,
      labelTransform: config.labelRotate ? `rotate(${config.labelRotate}rad)` : undefined,
      tickCount: config.tickCount,
    },
    y: {
      labelFontSize: config.fontSize,
    },
  },
});
```

## Responsive Handling in React/Vue Components

```javascript
// React Example (using useEffect and ref)
import { useEffect, useRef } from 'react';
import { Chart } from '@antv/g2';

function ResponsiveChart({ data }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = new Chart({
      container,
      autoFit: true,
      height: 400,
    });

    chart.options({ type: 'line', data, encode: { x: 'date', y: 'value' } });
    chart.render();
    chartRef.current = chart;

    const ro = new ResizeObserver(() => {
      chartRef.current?.forceFit();
    });
    ro.observe(container);

    return () => {
      ro.disconnect();
      chartRef.current?.destroy();
    };
  }, []);

  useEffect(() => {
    chartRef.current?.changeData(data);
  }, [data]);

  return <div ref={containerRef} style={{ width: '100%', height: 400 }} />;
}
```

## Common Mobile Adaptations

```javascript
const isMobile = window.matchMedia('(max-width: 768px)').matches;

chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value' },
  // Mobile: Convert to horizontal bar chart (category labels are more readable)
  coordinate: isMobile ? [{ type: 'transpose' }] : undefined,
  // Mobile: Reduce tick count
  axis: {
    x: { tickCount: isMobile ? 4 : 8 },
    y: {
      labelFontSize: isMobile ? 10 : 12,
      title: isMobile ? null : 'Value',   // Hide axis title on mobile to save space
    },
  },
  // Mobile: Hide legend (limited space)
  legend: isMobile ? false : { position: 'top' },
});
```

## Common Errors and Fixes

### Error 1: Initializing the Chart When the Container is `display:none`

```javascript
// ❌ Issue: When the container is hidden, `clientWidth = 0`, resulting in a chart with dimensions of 0
const chart = new Chart({ container: 'hidden-tab', autoFit: true });

// ✅ Solution: Initialize the chart when the container is visible, or call `changeSize` after it is displayed
container.style.display = 'block';
chart.changeSize(container.clientWidth, container.clientHeight);
```

### Error 2: Performance Issues Caused by Multiple Non-Debounced Resize Triggers

```javascript
// ❌ Immediate redraw on every resize (potentially triggered 60 times per second)
window.addEventListener('resize', () => {
  chart.changeSize(window.innerWidth * 0.8, 400);
});

// ✅ Debounce handling
window.addEventListener('resize', debounce(() => {
  chart.changeSize(window.innerWidth * 0.8, 400);
}, 300));
```