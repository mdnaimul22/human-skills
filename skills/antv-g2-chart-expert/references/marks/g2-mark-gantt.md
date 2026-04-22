---
id: "g2-mark-gantt"
title: "G2 Gantt Chart Mark"
description: |
  Gantt Chart Mark. Uses interval marks with a transpose coordinate system to display the scheduling of project tasks.
  Suitable for project management, task scheduling, progress tracking, and other scenarios.

library: "g2"
version: "5.x"
category: "marks"
tags:
  - "Gantt Chart"
  - "gantt"
  - "Project Management"
  - "Progress"

related:
  - "g2-mark-interval-basic"
  - "g2-comp-slider"

use_cases:
  - "Project Progress Management"
  - "Task Scheduling"
  - "Resource Management"

anti_patterns:
  - "Not suitable for non-time dimension data"
  - "Continuous numerical changes should use line charts"

difficulty: "beginner"
completeness: "full"
created: "2025-03-26"
updated: "2025-03-26"
author: "antv-team"
source_url: "https://g2.antv.antgroup.com/manual/core/mark/gantt"
---

## Core Concepts

Gantt charts display the scheduling of project tasks:
- Use `interval` marks
- Combine with `transpose` coordinate transformation
- `y` and `y1` represent start and end times

**Key Elements:**
- Task Name: Mapped to the horizontal axis
- Start Time: Mapped to `y`
- End Time: Mapped to `y1`

## Minimum Viable Example

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',
  theme: 'classic',
});

chart.options({
  type: 'interval',
  autoFit: true,
  data: [
    { name: 'Event Planning', startTime: 1, endTime: 4 },
    { name: 'Venue Planning', startTime: 3, endTime: 13 },
    { name: 'Vendor Selection', startTime: 5, endTime: 8 },
  ],
  encode: {
    x: 'name',
    y: 'startTime',
    y1: 'endTime',
    color: 'name',
  },
  coordinate: {
    transform: [{ type: 'transpose' }],
  },
});

chart.render();
```

## Common Variants

### With Project Phases

```javascript
chart.options({
  type: 'interval',
  data: [
    { name: 'Requirement Analysis', startTime: 1, endTime: 5, phase: 'Planning' },
    { name: 'System Design', startTime: 4, endTime: 10, phase: 'Design' },
    { name: 'Front-end Development', startTime: 8, endTime: 20, phase: 'Development' },
  ],
  encode: {
    x: 'name',
    y: 'startTime',
    y1: 'endTime',
    color: 'phase',  // Color by phase
  },
  coordinate: { transform: [{ type: 'transpose' }] },
});
```

### With Timing Animation

```javascript
chart.options({
  type: 'interval',
  data,
  encode: {
    x: 'name',
    y: 'startTime',
    y1: 'endTime',
    color: 'name',
    enterDuration: (d) => (d.endTime - d.startTime) * 200,
    enterDelay: (d) => d.startTime * 100,
  },
  coordinate: { transform: [{ type: 'transpose' }] },
});
```

### With Milestones

```javascript
chart.options({
  type: 'view',
  children: [
    {
      type: 'interval',
      data: tasks,
      encode: { x: 'name', y: 'startTime', y1: 'endTime' },
      coordinate: { transform: [{ type: 'transpose' }] },
    },
    {
      type: 'point',
      data: milestones,
      encode: {
        x: 'name',
        y: 'time',
        shape: 'diamond',
        size: 8,
      },
      coordinate: { transform: [{ type: 'transpose' }] },
    },
  ],
});
```

## Complete Type Reference

```typescript
interface GanttData {
  name: string;        // Task name
  startTime: number;   // Start time
  endTime: number;     // End time
  phase?: string;      // Project phase
}

interface GanttOptions {
  type: 'interval';
  encode: {
    x: string;         // Task name field
    y: string;         // Start time field
    y1: string;        // End time field
    color?: string;    // Color field
  };
  coordinate: {
    transform: [{ type: 'transpose' }];
  };
}
```

## Gantt Chart vs Bar Chart

| Feature | Gantt Chart | Bar Chart |
|---------|----------------|----------------|
| Purpose | Task Scheduling | Numerical Comparison |
| Data Dimension | Time Interval | Single Value |
| Visual Form | Horizontal Bar | Vertical Bar |

## Common Errors and Fixes

### Error 1: Missing transpose

```javascript
// ❌ Problem: Default is vertical direction
coordinate: {}

// ✅ Correct: Add transpose
coordinate: { transform: [{ type: 'transpose' }] }
```

### Error 2: Missing y1 Encoding

```javascript
// ❌ Problem: Only start time is encoded
encode: { x: 'name', y: 'startTime' }

// ✅ Correct: Add end time
encode: { x: 'name', y: 'startTime', y1: 'endTime' }
```

### Error 3: Too Many Tasks

```javascript
// ⚠️ Note: It is recommended to have no more than 20 tasks
// Excessive tasks can lead to chart congestion
```