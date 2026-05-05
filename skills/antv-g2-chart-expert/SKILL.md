---
name: antv-g2-chart
description: Generate G2 v5 chart code. Use when user asks for G2 charts, bar charts, line charts, pie charts, scatter plots, area charts, or any data visualization with G2 library.
---

# G2 v5 Chart Code Generator

You are an expert in AntV G2 v5 charting library. Generate accurate, runnable code following G2 v5 best practices.

---

## 1. Core Constraints (MUST follow)

1. **`container` is mandatory**: `new Chart({ container: 'container', ... })`
2. **Use Spec Mode ONLY**: `chart.options({ type: 'interval', data, encode: {...} })` (See Forbidden Patterns for V4 chained API)
3. **`chart.options()` can only be called once**: Multiple calls will completely overwrite the previous configuration, only the last call takes effect. For multiple mark overlays, use `type: 'view'` + `children` array instead of multiple calls to `chart.options()`
4. **`encode` object**: `encode: { x, y }` (V4's `.position('x*y')` is forbidden)
5. **`transform` must be array**: `transform: [{ type: 'stackY' }]`
6. **`labels` is plural**: Use `labels: [{ text: 'field' }]` not `label: {}`
7. **`coordinate` rules**:
   - Directly specify coordinate type: `coordinate: { type: 'theta' }`, `coordinate: { type: 'polar' }`
   - `transpose` is a **transformation**, not a coordinate type, and must be placed in the `transform` array: `coordinate: { transform: [{ type: 'transpose' }] }`
   - ❌ Forbidden: `coordinate: { type: 'transpose' }`
8. **Range encoding** (Gantt chart, candlestick, etc.): `encode: { y: 'start', y1: 'end' }`, forbidden: `y: ['start', 'end']`
9. **Style principles**: Styles mentioned in the user description (radius, fillOpacity, color, fontSize, etc.) must be fully preserved; do not add decorative styles not mentioned by the user (shadowBlur, shadowColor, shadowOffsetX/Y, etc.)
10. **`animate` rules**: Do not add `animate` configuration when the user does not explicitly request animation (G2 has default animations built-in), only add when the user explicitly describes animation requirements
11. **`scale.color.palette` can only use valid values**: Palette is looked up via d3-scale-chromatic, invalid names will throw `Unknown palette` error. **Do not infer or create non-existent names** (e.g., `'blueOrange'`, `'redGreen'`, `'hot'`, `'jet'`, `'coolwarm'` are all invalid). Common valid values: sequential color scales `'blues'|'greens'|'reds'|'ylOrRd'|'viridis'|'plasma'|'turbo'`; diverging color scales `'rdBu'|'rdYlGn'|'spectral'`; when unsure, use `range: ['#startColor', '#endColor']` for custom replacement
12. **Forbidden to use `d3.*` in user code**: G2 internally uses d3, but the `d3` object is not exposed to the user code scope, calling `d3.sum()` etc. will throw `ReferenceError: d3 is not defined`. For aggregation, prioritize using G2 built-in options (e.g., `sortX`'s `reducer: 'sum'`), when custom aggregation is necessary, use native JS: `d3.sum(arr, d=>d.v)` → `arr.reduce((s,d)=>s+d.v,0)`; `d3.max(arr, d=>d.v)` → `Math.max(...arr.map(d=>d.v))`
13. **When the user does not specify a color scheme, do not use white or near-white as the shape fill color**: `style: { fill: '#fff' }`, `style: { fill: 'white' }`, `style: { fill: '#ffffff' }` etc. will make the shape completely invisible on a white background. When no color scheme is specified, rely on G2's `encode.color` to automatically assign theme colors, or use colors with clear visual distinction (e.g., `'#5B8FF9'`). The following are valid exceptions: label text `fill: '#fff'` (labels within dark backgrounds), separator lines `stroke: '#fff'` (white separator lines in stacked/pack/treemap)
14. **`padding` only accepts `number | 'auto'`, array form is forbidden**: `padding: [40, 30, 40, 50]` is invalid in G2 v5 (will be ignored or throw an error). For uniform padding, use `padding: 40`; for directional control, use `paddingTop` / `paddingRight` / `paddingBottom` / `paddingLeft` individually; default `'auto'` automatically reserves space for axes/legends, manual configuration is usually unnecessary. **Forbidden to set `padding: 0`**—this will disable automatic calculation, causing axes/legends to be truncated; when adjusting only one direction, set the corresponding direction individually
15. **When `autoFit: true`, do not set `width` simultaneously**: `autoFit` will completely ignore `width`, rendering it ineffective when both are present. When `autoFit: true`, set only `height`; when fixed width and height are needed, remove `autoFit` and use `width` + `height` instead
16. **When the user does not specify a container**: `container` defaults to `'container'`, do not create via `document.createElement('div')`, the code must end with `chart.render();`

### 1.1 Forbidden Patterns

**Forbidden: V4 Syntax**, Must use V5 Spec Mode:


```javascript
// ❌ Forbidden: V4 createView
const view = chart.createView();
view.options({...});

// ❌ Forbidden: V4 Chained API Calls
chart.interval()
  .data([...])
  .encode('x', 'genre')
  .encode('y', 'sold')
  .style({ radius: 4 });

// ❌ Forbidden: V4 Chained encode
chart.line().encode('x', 'date').encode('y', 'value');

// ❌ Forbidden: V4 source
chart.source(data);

// ❌ Forbidden: V4 position
chart.interval().position('genre*sold');

// ✅ Correct: V5 Spec Mode
chart.options({
  type: 'interval',
  data: [...],
  encode: { x: 'genre', y: 'sold' },
  style: { radius: 4 },
});
```

**Reason**: V5 uses Spec mode, which has a clear structure and is easy to serialize, dynamically generate, and debug.

#### Correct V5 Alternative for `createView`

`chart.createView()` in V4 was used for "multiple views sharing a container but with different data". In V5, it corresponds to two scenarios:

**Scenario A: Multiple marks stacked within the same coordinate system (most common)**
→ Use `type: 'view'` + `children` array, `children` cannot be nested with `view` or `children`:

```javascript
// ✅ Multiple marks stacked (line + point)
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'line',  encode: { x: 'date', y: 'value' } },
    { type: 'point', encode: { x: 'date', y: 'value' } },
  ],
});
```

**Scenario B: Multiple independent coordinate systems side by side or stacked (e.g., population pyramid, butterfly chart)**
→ Use `type: 'spaceLayer'` + `children` (each child view has independent data and coordinate system):

```javascript
// ✅ Population Pyramid: Two independent views stacked, sharing the Y-axis
chart.options({
  type: 'spaceLayer',
  children: [
    {
      type: 'interval',
      data: leftData,                              // Left data (negative values or flipped)
      coordinate: { transform: [{ type: 'transpose' }, { type: 'reflectX' }] },
      encode: { x: 'age', y: 'male' },
      axis: { y: { position: 'right' } },
    },
    {
      type: 'interval',
      data: rightData,                             // Right data
      coordinate: { transform: [{ type: 'transpose' }] },
      encode: { x: 'age', y: 'female' },
      axis: { y: false },
    },
  ],
});

// ✅ Simpler approach: Single view + negative value trick (data can be in one array)
chart.options({
  type: 'interval',
  data: combinedData,                              // Combined data, using negative values to distinguish direction
  coordinate: { transform: [{ type: 'transpose' }] },
  encode: {
    x: 'age',
    y: (d) => d.sex === 'male' ? -d.population : d.population,
    color: 'sex',
  },
  axis: {
    y: { labelFormatter: (d) => Math.abs(d) },     // Display absolute values
  },
});
```

**Selection Principle**:
- If both sides have the same data structure but opposite directions → **Prioritize negative value trick** (single `interval`, most concise code)
- If both sides require completely independent coordinate systems/scales → Use `spaceLayer`

### 1.2 Prohibited Hallucinated Mark Types

The following types are from other charting libraries (such as ECharts, Vega) and **do not exist in G2**. Using them will result in runtime errors:

| ❌ Incorrect Usage | ✅ Correct Replacement |
|--------------------|------------------------|
| `type: 'ruleX'`    | `type: 'lineX'` (vertical reference line) |
| `type: 'ruleY'`    | `type: 'lineY'` (horizontal reference line) |
| `type: 'regionX'`  | `type: 'rangeX'` (X-axis range highlight) |
| `type: 'regionY'`  | `type: 'rangeY'` (Y-axis range highlight) |
| `type: 'venn'`     | `type: 'path'` + `data.transform: [{ type: 'venn' }]` |

**Complete List of Valid Mark Types in G2** (do not create other types arbitrarily):
- Basic: `interval`, `line`, `area`, `point`, `rect`, `cell`, `text`, `image`, `path`, `polygon`, `shape`
- Connections: `link`, `connector`, `vector`
- Reference Lines/Areas: `lineX`, `lineY`, `rangeX`, `rangeY`; `range` (rarely used, only when both x/y need to define a 2D rectangle, and the x/y fields of the data must be `[start, end]` arrays)
- Statistical: `box`, `boxplot`, `density`, `heatmap`, `beeswarm`
- Hierarchical/Relational: `treemap`, `pack`, `partition`, `tree`, `sankey`, `chord`, `forceGraph`
- Special: `wordCloud`, `gauge`, `liquid`
- Requires Extension Package: `sunburst` (requires `@antv/g2-extension-plot`, see [Sunburst Chart](references/marks/g2-mark-sunburst.md))
---

## 2. Common Mistakes

### ⚠️ Most Frequent Error: Prohibit Multiple Calls to `chart.options()`

`chart.options()` is a **full replacement**, not a merge. When called multiple times, **only the last call takes effect**, and all previous configurations are lost. **Each chart can only call `chart.options()` once.**

```javascript
// ❌ Wrong: Multiple calls to chart.options() —— Each call fully replaces the previous one, only the last call takes effect
chart.options({ type: 'interval', data, encode: { x: 'x', y: 'y' } });  // ❌ Overwritten, not rendered
chart.options({ type: 'line',     data, encode: { x: 'x', y: 'y' } });  // ❌ Overwritten, not rendered
chart.options({ type: 'text',     data, encode: { x: 'x', y: 'y', text: 'label' } });  // Only this takes effect

// ✅ Correct: Multiple marks must use type: 'view' + children, resolved in one chart.options() call
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'interval', encode: { x: 'x', y: 'y' } },
    { type: 'line',     encode: { x: 'x', y: 'y' } },
    { type: 'text',     encode: { x: 'x', y: 'y', text: 'label' } },
  ],
});

// ✅ When child marks require different data, specify data separately within children
chart.options({
  type: 'view',
  data: mainData,
  children: [
    { type: 'interval', encode: { x: 'x', y: 'y' } },
    { type: 'text', data: labelData, encode: { x: 'x', text: 'label' } },
  ],
});
```

Multi-mark combination rules:
- Only use `children`, prohibit `marks`, `layers`, etc.
- `children` cannot be nested (`children` cannot contain `type: 'view'` + `children`)
- Use `spaceLayer`/`spaceFlex` for complex multi-coordinate system combinations

```javascript
// ❌ Wrong: Using marks/layers (prohibited)
chart.options({ type: 'view', data, marks: [...] });   // ❌
chart.options({ type: 'view', data, layers: [...] });  // ❌

// ❌ Wrong: Nested children (prohibited)
chart.options({ type: 'view', children: [{ type: 'view', children: [...] }] });  // ❌

// ✅ Correct: Use spaceLayer for complex multi-coordinate system combinations
chart.options({
  type: 'spaceLayer',
  children: [
    { type: 'view', children: [...] },
    { type: 'line', encode: { x: 'x', y: 'y' } },
  ],
});
```

### Other Common Errors

```javascript
// ❌ Wrong: padding in array form (CSS shorthand), not supported in G2 v5, will be ignored
const chart = new Chart({ container: 'container', padding: [40, 30, 40, 50] });  // ❌

// ✅ Correct: Uniform padding for all sides
const chart = new Chart({ container: 'container', padding: 40 });

// ✅ Correct: Padding controlled by direction
const chart = new Chart({ container: 'container', paddingTop: 40, paddingLeft: 60 });

// ❌ Wrong: Missing container
const chart = new Chart({ width: 640, height: 480 });

// ✅ Correct: Container required
const chart = new Chart({ container: 'container', width: 640, height: 480 });

// ❌ Wrong: Transform as object
chart.options({ transform: { type: 'stackY' } });

// ✅ Correct: Transform as array
chart.options({ transform: [{ type: 'stackY' }] });

// ❌ Wrong: Label (singular)
chart.options({ label: { text: 'value' } });

// ✅ Correct: Labels (plural)
chart.options({ labels: [{ text: 'value' }] });

// ❌ Wrong: Unnecessary scale type specification
chart.options({ scale: { x: { type: 'linear' }, y: { type: 'linear' } } });

// ✅ Correct: Let G2 infer scale type automatically
chart.options({ scale: { y: { domain: [0, 100] } } });
```

<!-- CONSTRAINTS:END -->

---

## 3. Basic Structure

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({ container: 'container', width: 640, height: 480 });

chart.options({
  type: 'interval',           // Mark type
  data: [...],                // Data array
  encode: { x: 'field', y: 'field', color: 'field' },
  transform: [],              // Data transforms
  scale: {},                  // Scale config
  coordinate: {},             // Coordinate system
  style: {},                  // Style config
  labels: [],                 // Data labels
  tooltip: {},                // Tooltip config
  axis: {},                   // Axis config
  legend: {},                 // Legend config
});

chart.render();
```

---

## 4. Core Concepts

Core concepts are the foundation of G2, and understanding them is a prerequisite for using G2 correctly.

### 4.1 Chart Initialization

Chart is the core class of G2, and all charts start from a Chart instance.

```javascript
import { Chart } from '@antv/g2';

const chart = new Chart({
  container: 'container',  // Required: DOM container ID or element
  width: 640,              // Optional: width
  height: 480,             // Optional: height
  autoFit: true,           // Optional: auto-fit container size
  padding: 'auto',         // Optional: padding
  theme: 'light',          // Optional: theme
});
```

> **Detailed Documentation**: [Chart Initialization](references/core/g2-core-chart-init.md)

### 4.2 encode Channel System

encode maps data fields to visual channels and is a core concept in G2.

| Channel | Usage | Example |
|------|------|------|
| `x` | X-axis position | `encode: { x: 'month' }` |
| `y` | Y-axis position | `encode: { y: 'value' }` |
| `color` | Color | `encode: { color: 'category' }` |
| `size` | Size | `encode: { size: 'population' }` |
| `shape` | Shape | `encode: { shape: 'type' }` |

> **Detailed Documentation**: [encode Channel System](references/core/g2-core-encode-channel.md)

### 4.3 View Composition (view + children)

Use the `view` type in conjunction with the `children` array to compose multiple marks.

```javascript
chart.options({
  type: 'view',
  data,
  children: [
    { type: 'line', encode: { x: 'date', y: 'value' } },
    { type: 'point', encode: { x: 'date', y: 'value' } },
  ],
});
```

> **Detailed Documentation**: [View Composition](references/core/g2-core-view-composition.md)

---

## 5. Concepts / Concept Guide

The concept guide helps in selecting the correct chart type and configuration scheme.

### 5.1 Chart Selection

Select the appropriate chart type based on data characteristics and visualization goals:

| Data Relationship | Recommended Chart | Mark |
|---------|---------|------|
| Comparison | Bar Chart, Column Chart | `interval` |
| Trend | Line Chart, Area Chart | `line`, `area` |
| Proportion | Pie Chart, Ring Chart | `interval` + `theta` |
| Distribution | Histogram, Box Plot | `rect`, `boxplot` |
| Correlation | Scatter Plot, Bubble Chart | `point` |
| Hierarchy | Treemap, Partition Chart, Sunburst Chart | `treemap`, `partition`, `sunburst` (requires extension package) |

> **Detailed Documentation**: [Chart Selection Guide](references/concepts/g2-concept-chart-selection.md)

### 5.2 Visual Channels / Visual Channels

Visual channels are the mapping methods from data to visual attributes:

| Channel Type | Suitable Data | Perceptual Accuracy |
|--------------|---------------|---------------------|
| Position     | Continuous/Discrete | Highest |
| Length       | Continuous     | High    |
| Color (Hue)  | Discrete       | Medium  |
| Color (Luminance) | Continuous | Medium  |
| Size         | Continuous     | Medium-Low |
| Shape        | Discrete       | Low     |

> **Detailed Documentation**: [Visual Channels](references/concepts/g2-concept-visual-channels.md)

### 5.3 Color Theory

Selecting an appropriate color scheme enhances chart readability:

| Scenario | Recommended Scheme | Example |
|----------|--------------------|---------|
| Categorical Data | Discrete Palette | `category10`, `category20` |
| Continuous Data | Sequential Palette | `Blues`, `RdYlBu` |
| Positive/Negative Contrast | Diverging Palette | `RdYlGn` |

> **Detailed Documentation**: [Color Theory](references/concepts/g2-concept-color-theory.md)

---

## 6. Marks / Chart Types

Marks are the core visualization elements in G2, determining the visual representation of data. Each Mark is suitable for specific data types and visualization scenarios.

### 6.1 Bar Chart Series / Interval

Bar charts are used to compare the magnitude of categorical data and are one of the most commonly used chart types. Basic bar charts use the `interval` mark, stacked bar charts require the addition of the `stackY` transform, and grouped bar charts use the `dodgeX` transform.

| Type | Mark | Key Configuration |
|------|------|----------|
| Basic Bar Chart | `interval` | - |
| Stacked Bar Chart | `interval` | `transform: [{ type: 'stackY' }]` |
| Grouped Bar Chart | `interval` | `transform: [{ type: 'dodgeX' }]` |
| Percentage Bar Chart | `interval` | `transform: [{ type: 'normalizeY' }]` |
| Horizontal Bar Chart | `interval` | `coordinate: { transform: [{ type: 'transpose' }] }` |

> **Detailed Documentation**: [Basic Bar Chart](references/marks/g2-mark-interval-basic.md) | [Stacked Bar Chart](references/marks/g2-mark-interval-stacked.md) | [Grouped Bar Chart](references/marks/g2-mark-interval-grouped.md) | [Percentage Bar Chart](references/marks/g2-mark-interval-normalized.md)

### 6.2 Line Chart Series / Line

Line charts are used to display the trend of data changes over time or ordered categories. They support single lines, multi-line comparisons, and different interpolation methods.

| Type | Mark | Key Configuration |
|------|------|----------|
| Basic Line Chart | `line` | - |
| Multi-Series Line | `line` | `encode: { color: 'category' }` |
| Smooth Curve | `line` | `encode: { shape: 'smooth' }` |
| Step Line | `line` | `encode: { shape: 'step' }` |

> **Detailed Documentation**: [Basic Line Chart](references/marks/g2-mark-line-basic.md) | [Multi-Series Line](references/marks/g2-mark-line-multi.md) | [LineX/LineY](references/marks/g2-mark-linex-liney.md)

### 6.3 Area Chart Series / Area

Area charts build upon line charts by filling the area beneath the line, emphasizing the magnitude of change over time. Stacked area charts are used to show the contribution of each part to the whole.

| Type | Mark | Key Configuration |
|------|------|----------|
| Basic Area Chart | `area` | - |
| Stacked Area Chart | `area` | `transform: [{ type: 'stackY' }]` |

> **Detailed Documentation**: [Basic Area Chart](references/marks/g2-mark-area-basic.md) | [Stacked Area Chart](references/marks/g2-mark-area-stacked.md)

### 6.4 Pie Chart/Donut Chart / Arc (Pie/Donut)

Pie charts are used to display the proportional relationship of parts to the whole. They are implemented using the `theta` coordinate system in conjunction with the `interval` mark.

| Type | Mark | Key Configuration |
|------|------|----------|
| Pie Chart | `interval` | `coordinate: { type: 'theta' }` + `stackY` |
| Donut Chart | `interval` | `coordinate: { type: 'theta', innerRadius: 0.6 }` |

> **Detailed Documentation**: [Pie Chart](references/marks/g2-mark-arc-pie.md) | [Donut Chart](references/marks/g2-mark-arc-donut.md)

### 6.5 Scatter Plot/Bubble Plot / Point

Scatter plots are used to display the relationship between two numerical variables, while bubble plots use the size of the points to represent a third dimension.

| Type | Mark | Key Configuration |
|------|------|----------|
| Scatter Plot | `point` | `encode: { x, y }` |
| Bubble Plot | `point` | `encode: { x, y, size }` |

> **Detailed Documentation**: [Scatter Plot](references/marks/g2-mark-point-scatter.md) | [Bubble Plot](references/marks/g2-mark-point-bubble.md)

### 6.6 Histogram

Histograms are used to display the distribution of continuous numerical data, implemented using the `rect` mark with the `binX` transform. Unlike bar charts, histograms have no gaps between bars, representing continuous data.

| Type | Mark | Key Configuration |
|------|------|----------|
| Basic Histogram | `rect` | `transform: [{ type: 'binX', y: 'count' }]` |
| Multi-Distribution Comparison | `rect` | `groupBy` grouping |

> **Detailed Documentation**: [Histogram](references/marks/g2-mark-histogram.md)

### 6.7 Rose Chart / Radial Bar Chart / Polar Charts

Charts under the polar coordinate system, representing numerical values through radius or arc length, are visually more appealing.

| Type | Mark | Key Configuration |
|------|------|----------|
| Rose Chart | `interval` | `coordinate: { type: 'polar' }` |
| Radial Bar Chart | `interval` | `coordinate: { type: 'radial' }` |

> **Detailed Documentation**: [Rose Chart](references/marks/g2-mark-rose.md) | [Radial Bar Chart](references/marks/g2-mark-radial-bar.md)

### 6.8 Distribution

Charts that display data distribution characteristics, suitable for statistical analysis and exploratory data analysis.

| Type | Mark | Usage |
|------|------|------|
| Boxplot | `boxplot` | Data distribution statistics |
| Box (Boxplot) | `box` | Manually specified boxplot with five-number summary |
| Density Plot | `density` | Kernel density estimation curve |
| Violin Plot | `density` + `boxplot` | Density distribution + statistical information |
| Polygon | `polygon` | Custom polygon area |

> **Detailed Documentation**: [Boxplot](references/marks/g2-mark-boxplot.md) | [Box (Boxplot)](references/marks/g2-mark-box-boxplot.md) | [Density Plot](references/marks/g2-mark-density.md) | [Violin Plot](references/marks/g2-mark-violin.md) | [Polygon](references/marks/g2-mark-polygon.md)

### 6.9 Relation

Charts that display relationships between data, suitable for network analysis and set relationship visualization.

| Type | Mark | Use Case |
|------|------|----------|
| Sankey Diagram | `sankey` | Flow/transfer relationships |
| Chord Diagram | `chord` | Matrix flow relationships |
| Venn Diagram | `path` + venn data transform | Set intersection relationships (venn is a data transform, not a mark type) |
| Arc Diagram | `line` + `point` | Node link relationships |

> **Detailed Documentation**: [Sankey Diagram](references/marks/g2-mark-sankey.md) | [Chord Diagram](references/marks/g2-mark-chord.md) | [Venn Diagram](references/marks/g2-mark-venn.md) | [Arc Diagram](references/marks/g2-mark-arc-diagram.md)

### 6.10 Project Management Chart / Project

Suitable for project management and progress tracking.

| Type | Mark | Usage |
|------|------|------|
| Gantt Chart | `interval` | Task scheduling |
| Bullet Chart | `interval` + `point` | KPI metric display |

> **Detailed Documentation**: [Gantt Chart](references/marks/g2-mark-gantt.md) | [Bullet Chart](references/marks/g2-mark-bullet.md)

### 6.11 Finance

Professional charts for financial data analysis.

| Type | Mark | Usage |
|------|------|------|
| K-line Chart | `link` + `interval` | Stock four-price data |

> **Detailed Documentation**: [K-line Chart](references/marks/g2-mark-k-chart.md)

### 6.12 Multivariate Data Chart / Multivariate

Charts for displaying multivariate data relationships.

| Type | Mark | Use Case |
|------|------|----------|
| Parallel Coordinates | `line` | Multivariate data relationship analysis |
| Radar Chart | `line` | Multivariate data comparison |

> **Detailed Documentation**: [Parallel Coordinates](references/marks/g2-mark-parallel.md) | [Radar Chart](references/marks/g2-mark-radar.md)

### 6.13 Comparison Chart / Comparison

Suitable for data comparison.

| Type | Mark | Usage |
|------|------|------|
| Bi-directional Bar Chart | `interval` | Positive and negative data comparison |

> **Detailed Documentation**: [Bi-directional Bar Chart](references/marks/g2-mark-bi-directional-bar.md)

### 6.14 Basic Marks

Basic marks are the foundational building blocks of G2, which can be used independently or combined to construct complex charts.

| Type | Mark | Usage |
|------|------|------|
| Rectangle | `rect` | Rectangular area, basis for histograms/heatmaps |
| Text | `text` | Text annotations and labels |
| Image | `image` | Image mark, representing data points with images |
| Path | `path` | Custom path drawing |
| Link | `link` | Line connecting two points |
| Connector | `connector` | Connection line between data points |
| Shape | `shape` | Custom shape drawing |
| Vector | `vector` | Vector/arrow mark, for wind field charts, etc. |

> **Detailed Documentation**: [rect](references/marks/g2-mark-rect.md) | [text](references/marks/g2-mark-text.md) | [image](references/marks/g2-mark-image.md) | [path](references/marks/g2-mark-path.md) | [link](references/marks/g2-mark-link.md) | [connector](references/marks/g2-mark-connector.md) | [shape](references/marks/g2-mark-shape.md) | [vector](references/marks/g2-mark-vector.md)

### 6.15 Range Mark / Range

The range mark is used to display the interval range of data.

| Type | Mark | Usage |
|------|------|------|
| Time Period/Interval Highlight (X Direction) | `rangeX` | X-axis interval, `encode: { x: 'start', x1: 'end' }` |
| Numerical Range Highlight (Y Direction) | `rangeY` | Y-axis interval, `encode: { y: 'min', y1: 'max' }` |
| Two-Dimensional Rectangular Area | `range` | x/y fields are `[start,end]` arrays, `encode: { x:'x', y:'y' }`, rarely used |

> **Detailed Documentation**: [range/rangeY](references/marks/g2-mark-range-rangey.md) | [rangeX](references/marks/g2-mark-rangex.md)

### 6.16 Distribution & Pack

| Type | Mark | Usage |
|------|------|------|
| Beeswarm Plot | `point` + `pack` | Closely arranged data points to display distribution |
| Pack Layout | `pack` | Circular packing for hierarchical data |

> **Detailed Documentation**: [Beeswarm Plot](references/marks/g2-mark-beeswarm.md) | [Pack Layout](references/marks/g2-mark-pack.md)

### 6.17 Hierarchy

Charts for displaying hierarchical data, representing numerical proportions through area or radius.

| Type | Mark | Usage |
|------|------|------|
| Treemap | `treemap` | Hierarchical data proportion |
| Sunburst | `sunburst`⚠️ | Multi-level concentric circle display (requires @antv/g2-extension-plot) |
| Partition | `partition` | Hierarchical data partition display |
| Tree | `tree` | Tree-like hierarchical structure |

> **Detailed Documentation**: [Treemap](references/marks/g2-mark-treemap.md) | [Sunburst](references/marks/g2-mark-sunburst.md) | [Partition](references/marks/g2-mark-partition.md) | [Tree](references/marks/g2-mark-tree.md)

### 6.18 Other Charts / Others

| Type | Mark | Usage |
|------|------|------|
| Heatmap | `cell` | Visualization of two-dimensional matrix data |
| Density Heatmap | `heatmap` | Continuous density heatmap |
| Gauge | `gauge` | Metric progress display |
| Word Cloud | `wordCloud` | Text frequency visualization |
| Liquid Fill Gauge | `liquid` | Percentage progress |

> **Detailed Documentation**: [Heatmap](references/marks/g2-mark-cell-heatmap.md) | [Density Heatmap](references/marks/g2-mark-heatmap.md) | [Gauge](references/marks/g2-mark-gauge.md) | [Word Cloud](references/marks/g2-mark-wordcloud.md) | [Liquid Fill Gauge](references/marks/g2-mark-liquid.md)

---

## 7. Data / Data Transformation

Data transformation is performed during the data loading stage and is configured in `data.transform`, affecting all marks that use this data.

### 7.1 Data Transform Types (Configured in `data.transform`)

| Transform | Type | Purpose | Example Scenario |
|------|------|------|---------|
| **fold** | `fold` | Wide table to long table | Convert multi-column data to multiple series |
| **filter** | `filter` | Conditional data filtering | Filter invalid data |
| **sort** | `sort` | Sort using a callback function | Custom sorting logic |
| **sortBy** | `sortBy` | Sort by field | Sort by field values |
| **map** | `map` | Data mapping transformation | Add computed fields |
| **join** | `join` | Merge data tables | Associate external data |
| **pick** | `pick` | Select specified fields | Simplify fields |
| **rename** | `rename` | Rename fields | Field renaming |
| **slice** | `slice` | Slice data range | Pagination/slicing |
| **ema** | `ema` | Exponential Moving Average | Time series smoothing |
| **kde** | `kde` | Kernel Density Estimation | Density plot/violin plot |
| **log** | `log` | Print data to console | Debugging |
| **custom** | `custom` | Custom data processing | Complex transformations |

### 7.2 Data Format and Patterns

| Type | Purpose |
|------|------|
| Tabular Data Format | Description of the standard tabular data format accepted by G2 |
| Data Transformation Patterns | Combination usage patterns of Data Transform and Mark Transform |

> **Detailed Documentation**: [filter](references/data/g2-data-filter.md) | [sort](references/data/g2-data-sort.md) | [sortBy](references/data/g2-data-sortby.md) | [fold](references/data/g2-data-fold.md) | [slice](references/data/g2-data-slice.md) | [ema](references/data/g2-data-ema.md) | [kde](references/data/g2-data-kde.md) | [log](references/data/g2-data-log.md) | [fetch](references/data/g2-data-fetch.md) | [Data Transformation Patterns](references/data/g2-data-transform-patterns.md)

### 7.3 Common Mistakes: Incorrect Placement of Data Transform

```javascript
// ❌ Wrong: fold is a data transform and cannot be placed in mark transform
chart.options({
  type: 'interval',
  data: wideData,
  transform: [{ type: 'fold', fields: ['a', 'b'] }],  // ❌ Wrong!
});

// ✅ Correct: fold placed in data.transform
chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: wideData,
    transform: [{ type: 'fold', fields: ['a', 'b'] }],  // ✅ Correct
  },
  transform: [{ type: 'stackY' }],  // mark transform
});
```

### 7.4 Combination Example: Wide Table Data + Stacked Chart

```javascript
// Wide table data: Multiple data columns for each month
const wideData = [
  { year: '2000', 'Type A': 21, 'Type B': 16, 'Type C': 8 },
  { year: '2001', 'Type A': 25, 'Type B': 16, 'Type C': 8 },
  // ...
];

chart.options({
  type: 'interval',
  data: {
    type: 'inline',
    value: wideData,
    transform: [
      // ✅ Data Transform: Wide to Long Table
      { type: 'fold', fields: ['Type A', 'Type B', 'Type C'], key: 'type', value: 'value' },
    ],
  },
  encode: { x: 'year', y: 'value', color: 'type' },
  transform: [
    // ✅ Mark Transform: Stacked
    { type: 'stackY' },
  ],
  coordinate: { type: 'polar' },  // Polar coordinate system
});
```

---

## 8. Transforms / Mark Transformations

Mark transformations are executed when binding visual channels and are configured in the `transform` array of the mark. They are used for data aggregation, anti-overlapping, and more.

**Configuration Location**: The `transform` array, which is at the same level as `data` and `encode`, **not** in `data.transform`.

```javascript
chart.options({
  type: 'interval',
  data,
  encode: { x: 'category', y: 'value', color: 'type' },
  transform: [  // ✅ Mark Transform: At the same level as data/encode
    { type: 'stackY' },
    { type: 'sortX', by: 'y' },
  ],
});
```

### 8.1 Anti-overlap Transformations

| Transformation | Type | Purpose |
|------|------|------|
| Stack | `stackY` | Data stacking, used for stacked charts |
| Dodge | `dodgeX` | Data grouping, used for dodged charts |
| Jitter | `jitter` | Scatter jitter to avoid overlap |
| Jitter X | `jitterX` | Jitter in the X direction |
| Jitter Y | `jitterY` | Jitter in the Y direction |
| Pack | `pack` | Tightly arrange data points |

> **Detailed Documentation**: [stackY](references/transforms/g2-transform-stacky.md) | [dodgeX](references/transforms/g2-transform-dodgex.md) | [jitter](references/transforms/g2-transform-jitter.md) | [jitterX](references/transforms/g2-transform-jitterx.md) | [jitterY](references/transforms/g2-transform-jittery.md) | [pack](references/transforms/g2-transform-pack.md)

### 8.2 Aggregation Transforms / Aggregation

| Transform | Type | Purpose |
|------|------|------|
| General Grouping | `group` | General grouping aggregation |
| Group Aggregation | `groupX` / `groupY` | Group and aggregate by dimension |
| Group Color | `groupColor` | Group aggregation by color |
| Binning | `bin` | Two-dimensional binning |
| X-axis Binning | `binX` | Binning in the X-axis direction |
| Sampling | `sample` | Data sampling |

> **Detailed Documentation**: [group](references/transforms/g2-transform-group.md) | [groupX](references/transforms/g2-transform-groupx.md) | [groupY](references/transforms/g2-transform-groupy.md) | [groupColor](references/transforms/g2-transform-groupcolor.md) | [bin](references/transforms/g2-transform-bin.md) | [binX](references/transforms/g2-transform-binx.md) | [sample](references/transforms/g2-transform-sample.md)

### 8.3 Sorting Transforms / Sorting

| Transform | Type | Purpose |
|------|------|------|
| X-axis Sorting | `sortX` | Sort by X channel |
| Y-axis Sorting | `sortY` | Sort by Y channel |
| Color Sorting | `sortColor` | Sort by color channel |

> **Detailed Documentation**: [sortX](references/transforms/g2-transform-sortx.md) | [sortY](references/transforms/g2-transform-sorty.md) | [sortColor](references/transforms/g2-transform-sort-color.md)

### 8.4 Selection Transforms / Selection

| Transform | Type | Purpose |
|------|------|------|
| Selection | `select` | Global data selection |
| X-axis Selection | `selectX` | Selection by X grouping |
| Y-axis Selection | `selectY` | Selection by Y grouping |

> **Detailed Documentation**: [select](references/transforms/g2-transform-select.md) | [selectX](references/transforms/g2-transform-selectx.md) | [selectY](references/transforms/g2-transform-selecty.md)

### 8.5 Other Transforms / Others

| Transform | Type | Usage |
|------|------|------|
| Normalize | `normalizeY` | Y-axis normalization |
| Difference | `diffY` | Calculate differences |
| Symmetry | `symmetryY` | Y-axis symmetry |
| Flex X | `flexX` | X-axis flex layout |
| Stack Enter | `stackEnter` | Stacked enter animation |

> **Detailed Documentation**: [normalizeY](references/transforms/g2-transform-normalizey.md) | [diffY](references/transforms/g2-transform-diffy.md) | [symmetryY](references/transforms/g2-transform-symmetryy.md) | [flexX](references/transforms/g2-transform-flexx.md) | [stackEnter](references/transforms/g2-transform-stack-enter.md)

---

## 9. Interactions

G2 provides a rich set of built-in interactions for data exploration and chart manipulation.

### 9.1 Selection Interactions

| Interaction | Type | Purpose |
|------|------|------|
| Element Selection | `elementSelect` | Click to select data elements |
| Conditional Selection | `elementSelectBy` | Batch select elements based on conditions |
| Brush Selection | `brush` / `brushX` / `brushY` | Rectangular area selection |
| 2D Brush Selection | `brushXY` | Simultaneous XY brush selection |
| Axis Brush Selection | `brushAxis` | Coordinate axis range selection |
| Legend Filter | `legendFilter` | Click legend to filter data |

> **Detailed Documentation**: [elementSelect](references/interactions/g2-interaction-element-select.md) | [elementSelectBy](references/interactions/g2-interaction-element-select-by.md) | [brush](references/interactions/g2-interaction-brush.md) | [brushXY](references/interactions/g2-interaction-brush-xy.md) | [brushAxis](references/interactions/g2-interaction-brush-axis.md) | [legendFilter](references/interactions/g2-interaction-legend-filter.md)

### 9.2 Highlight Interactions / Highlight

| Interaction | Type | Purpose |
|------|------|------|
| Element Highlight | `elementHighlight` | Hover to highlight elements |
| Conditional Highlight | `elementHighlightBy` | Batch highlight elements based on conditions |
| Hover Scale | `elementHoverScale` | Scale up elements on hover |
| Legend Highlight | `legendHighlight` | Hover legend to highlight corresponding elements |
| Brush Highlight | `brushXHighlight` / `brushYHighlight` | Highlight selected area |

> **Detailed Documentation**: [elementHighlight](references/interactions/g2-interaction-element-highlight.md) | [elementHighlightBy](references/interactions/g2-interaction-element-highlight-by.md) | [elementHoverScale](references/interactions/g2-interaction-element-hover-scale.md) | [legendHighlight](references/interactions/g2-interaction-legend-highlight.md) | [brushXHighlight](references/interactions/g2-interaction-brushx-highlight.md) | [brushYHighlight](references/interactions/g2-interaction-brushy-highlight.md) | [Single-axis Brush Highlight](references/interactions/g2-interaction-brush-x-y-highlight.md)

### 9.3 Filter Interactions / Filter

| Interaction | Type | Purpose |
|------|------|------|
| Slider Filter | `sliderFilter` | Filter data range using a slider |
| Scrollbar Filter | `scrollbarFilter` | Filter data using a scrollbar |
| Brush Filter | `brushFilter` | Filter data within a selected area |
| X-axis Brush Filter | `brushXFilter` | Filter data along the X-axis direction |
| Y-axis Brush Filter | `brushYFilter` | Filter data along the Y-axis direction |
| Adaptive Filter | `adaptiveFilter` | Adaptively filter data |

> **Detailed Documentation**: [sliderFilter](references/interactions/g2-interaction-slider-filter.md) | [scrollbarFilter](references/interactions/g2-interaction-scrollbar-filter.md) | [brushFilter](references/interactions/g2-interaction-brush-filter.md) | [brushXFilter](references/interactions/g2-interaction-brushx-filter.md) | [brushYFilter](references/interactions/g2-interaction-brushy-filter.md) | [adaptiveFilter](references/interactions/g2-interaction-adaptive-filter.md)

### 9.4 Other Interactions / Others

| Interaction | Type | Purpose |
|------|------|------|
| Tooltip | `tooltip` | Display data details on hover |
| PopTip | `poptip` | Concise pop-up tip |
| Drilldown | `drilldown` | Hierarchical data drilldown |
| Treemap Drilldown | `treemapDrilldown` | Treemap hierarchical drilldown |
| Fisheye | `fisheye` | Fisheye magnifier effect |
| Slider Wheel | `sliderWheel` | Mouse wheel control for slider |
| Element Point Move | `elementPointMove` | Drag data point to move |
| Chart Index | `chartIndex` | Multi-chart linkage index line |

> **Detailed Documentation**: [tooltip](references/interactions/g2-interaction-tooltip.md) | [poptip](references/interactions/g2-interaction-poptip.md) | [drilldown](references/interactions/g2-interaction-drilldown.md) | [treemapDrilldown](references/interactions/g2-interaction-treemap-drilldown.md) | [fisheye](references/interactions/g2-interaction-fisheye.md) | [sliderWheel](references/interactions/g2-interaction-slider-wheel.md) | [elementPointMove](references/interactions/g2-interaction-element-point-move.md) | [chartIndex](references/interactions/g2-interaction-chart-index.md)

---

## 10. Components / 组件

Components are auxiliary elements of charts, such as axes, legends, and tooltips.

### 10.1 Axis

The axis displays data dimensions and supports rich style configurations.

> **Detailed Documentation**: [Axis Configuration](references/components/g2-comp-axis-config.md) | [Radar Chart Axis](references/components/g2-comp-axis-radar.md)

### 10.2 Legend

The legend displays data categorization or continuous value mapping, supporting categorical legends and continuous legends (color ramps).

| Type | Purpose |
|------|------|
| Categorical Legend | Color mapping explanation for discrete categorical data |
| Continuous Legend | Color/size mapping explanation for continuous values (color ramp) |

> **Detailed Documentation**: [Legend Configuration](references/components/g2-comp-legend-config.md) | [Categorical Legend](references/components/g2-comp-legend-category.md) | [Continuous Legend](references/components/g2-comp-legend-continuous.md)

### 10.3 Tooltip

Tooltip displays data details on hover and supports custom templates and formatting.

> **Detailed Documentation**: [Tooltip Configuration](references/components/g2-comp-tooltip-config.md)

### 10.4 Other Components / Others

| Component | Purpose |
|-----------|---------|
| Title     | Chart title |
| Label     | Data label |
| Scrollbar | Data scrolling |
| Slider    | Data range selection |
| Annotation| Data annotation and auxiliary lines |

> **Detailed Documentation**: [Title](references/components/g2-comp-title.md) | [Label](references/components/g2-comp-label-config.md) | [Scrollbar](references/components/g2-comp-scrollbar.md) | [Slider](references/components/g2-comp-slider.md) | [Annotation](references/components/g2-comp-annotation.md)

---

## 11. Scales

Scales map data values to visual channels such as position, color, size, and more.

### 11.1 ⚠️ Default Behavior (Avoid Over-Specifying `type`)

**G2 automatically infers the scale type based on the data type. Avoid manually specifying `type` unless necessary:**

| Data Type | Inferred Scale | Example |
|-----------|----------------|---------|
| Numerical Field | `linear` | `{ value: 100 }` → linear |
| Categorical Field | `band` | `{ category: 'A' }` → band |
| Date Object | `time` | `{ date: new Date() }` → time |

```javascript
// ❌ Incorrect: Unnecessary type specification may cause rendering issues
chart.options({
  scale: {
    x: { type: 'linear' },  // ❌ Numerical fields default to linear
    y: { type: 'linear' },  // ❌ No need to specify
  },
});

// ✅ Correct: Let G2 infer automatically, configure domain/range only when needed
chart.options({
  scale: {
    y: { domain: [0, 100] },  // ✅ Configure only necessary properties
    color: { range: ['#1890ff', '#52c41a'] },
  },
});
```

**Special Cases Requiring Manual `type` Specification:**

| Scenario | Type | Description |
|----------|------|-------------|
| Logarithmic Scale | `log` | Data spanning multiple orders of magnitude |
| Power Scale | `pow` | Non-linear data mapping |
| Square Root Scale | `sqrt` | Compression of non-negative data |
| String Date | `time` | Date field is a string, not a Date object |
| Custom Mapping | `ordinal` | Discrete to discrete mapping |
| Gradient Color | `sequential` | Continuous values to color gradient |
| Threshold Mapping | `threshold` | Mapping by threshold to colors |
| Equal Interval Binning | `quantize` / `quantile` | Discretization of continuous data |

### 11.2 Scale Types

| Scale | Type | Usage |
|--------|------|------|
| Linear | `linear` | Continuous numerical mapping (default) |
| Band | `band` | Discrete categorical mapping (default) |
| Point | `point` | Discrete point position mapping |
| Time | `time` | Time data mapping |
| Log | `log` | Logarithmic scale |
| Power/Square Root | `pow` / `sqrt` | Power function/square root mapping |
| Ordinal | `ordinal` | Discrete to discrete value mapping |
| Sequential | `sequential` | Continuous value to color gradient |
| Quantile/Quantize | `quantile` / `quantize` | Continuous data discretization mapping |
| Threshold | `threshold` | Segmented mapping by threshold |

> **Detailed Documentation**: [linear](references/scales/g2-scale-linear.md) | [band](references/scales/g2-scale-band.md) | [point](references/scales/g2-scale-point.md) | [time](references/scales/g2-scale-time.md) | [log](references/scales/g2-scale-log.md) | [pow/sqrt](references/scales/g2-scale-pow-sqrt.md) | [ordinal](references/scales/g2-scale-ordinal.md) | [sequential](references/scales/g2-scale-sequential.md) | [quantile/quantize](references/scales/g2-scale-quantile-quantize.md) | [threshold](references/scales/g2-scale-threshold.md)

---

## 12. Coordinates / 坐标系

The coordinate system defines the mapping method from data to canvas position, and different coordinate systems produce different chart forms.

| Coordinate System | Type | Usage |
|-------------------|------|------|
| Cartesian | `cartesian` | Rectangular coordinate system (default) |
| Polar | `polar` | Radar chart, rose chart |
| Theta | `theta` | Pie chart, donut chart |
| Radial | `radial` | Radial coordinate system, gauge chart |
| Transpose | `transpose` | X/Y axis swap |
| Parallel | `parallel` | Parallel coordinate system |
| Helix | `helix` | Helix coordinate system |
| Fisheye | `fisheye` | Local magnification effect |

> **Detailed Documentation**: [cartesian](references/coordinates/g2-coord-cartesian.md) | [polar](references/coordinates/g2-coord-polar.md) | [theta](references/coordinates/g2-coord-theta.md) | [radial](references/coordinates/g2-coord-radial.md) | [transpose](references/coordinates/g2-coord-transpose.md) | [parallel](references/coordinates/g2-coord-parallel.md) | [helix](references/coordinates/g2-coord-helix.md) | [fisheye](references/coordinates/g2-coord-fisheye.md)

---

## 13. Compositions / Composition Views

Composition views are used to create multi-chart layouts, such as facets, multi-view overlays, etc.

| Composition | Type | Purpose |
|------|------|------|
| Basic View | `view` | Single view container, combining multiple marks |
| Facet Rect | `facetRect` | Split rectangular grid multi-chart by dimension |
| Facet Circle | `facetCircle` | Split circular multi-chart by dimension |
| Repeat Matrix | `repeatMatrix` | Multi-variable combination matrix chart |
| Space Layer | `spaceLayer` | Multi-layer overlay |
| Space Flex | `spaceFlex` | Flexible layout |
| Timing Keyframe | `timingKeyframe` | Animation sequence |
| Geo View | `geoView` | Geographic coordinate system view |
| Geo Path | `geoPath` | Geographic path rendering |

> **Detailed Documentation**: [view](references/compositions/g2-comp-view.md) | [facetRect](references/compositions/g2-comp-facet-rect.md) | [facetCircle](references/compositions/g2-comp-facet-circle.md) | [repeatMatrix](references/compositions/g2-comp-repeat-matrix.md) | [spaceLayer](references/compositions/g2-comp-space-layer.md) | [spaceFlex](references/compositions/g2-comp-space-flex.md) | [timingKeyframe](references/compositions/g2-comp-timing-keyframe.md) | [geoView](references/compositions/g2-comp-geoview.md) | [geoPath](references/compositions/g2-comp-geo-map.md)

---

## 14. Themes / 主题

Themes define the overall visual style of a chart, including colors, fonts, spacing, and more.

> **Detailed Documentation**: [Built-in Themes](references/themes/g2-theme-builtin.md) | [Custom Themes](references/themes/g2-theme-custom.md)

---
## 15. Palettes

Palettes define color sequences, used for color mapping of categorical or continuous data.

> **Detailed Documentation**: [category10](references/palette/g2-palette-category10.md) | [category20](references/palette/g2-palette-category20.md)

---

## 16. Animations

Animations enhance the expressiveness of charts, supporting entrance, update, and exit animation configurations.

**⚠️ Important Rule**: G2 comes with default animation effects at the underlying level. **Do not** add `animate` configurations unless the user explicitly requests animations. Only when the user clearly describes animation requirements (e.g., "fade-in animation", "wave entrance", etc.) should you refer to the documentation and add the corresponding animate configuration.

> **Detailed Documentation**: [Animation Introduction](references/animations/g2-animation-intro.md) | [Animation Types](references/animations/g2-animation-types.md) | [Keyframe Animation](references/animations/g2-animation-keyframe.md)

---

## 17. Label Transforms

Label transforms are used to handle issues such as label overlap and overflow, improving label readability.

| Transform | Type | Purpose |
|------|------|------|
| Overflow Hide | `overflowHide` | Hide labels that exceed the area |
| Overlap Hide | `overlapHide` | Automatically hide overlapping labels |
| Overlap Dodge Y | `overlapDodgeY` | Offset overlapping labels in the Y direction |
| Contrast Reverse | `contrastReverse` | Automatically reverse label colors to ensure contrast |
| Exceed Adjust | `exceedAdjust` | Adjust the position of labels that exceed the canvas boundaries |
| Overflow Stroke | `overflowStroke` | Add stroke marks to overflow areas |

> **Detailed Documentation**: [overflowHide](references/label-transform/g2-label-transform-overflow-hide.md) | [overlapHide](references/label-transform/g2-label-transform-overlap-hide.md) | [overlapDodgeY](references/label-transform/g2-label-transform-overlap-dodge-y.md) | [contrastReverse](references/label-transform/g2-label-transform-contrast-reverse.md) | [exceedAdjust](references/label-transform/g2-label-transform-exceed-adjust.md) | [overflowStroke](references/label-transform/g2-label-transform-overflow-stroke.md)

---

## 18. Patterns

Patterns are best practices for common scenarios, including migration guides, performance optimization, and responsive adaptation.
### 18.1 Migration Guide / Migration (v4 → v5)

| v4 (Deprecated) | v5 (Correct) |
|-----------------|--------------|
| `chart.source(data)` | `chart.options({ data })` |
| `.position('x*y')` | `encode: { x: 'x', y: 'y' }` |
| `.color('field')` | `encode: { color: 'field' }` |
| `.adjust('stack')` | `transform: [{ type: 'stackY' }]` |
| `.adjust('dodge')` | `transform: [{ type: 'dodgeX' }]` |
| `label: {}` | `labels: [{}]` |

> **Detailed Documentation**: [v4 → v5 Migration](references/patterns/g2-pattern-v4-to-v5.md)

### 18.2 Performance Optimization / Performance

Data pre-aggregation, LTTB downsampling, Canvas renderer confirmation, high-frequency real-time data throttling updates.

| Scenario | Data Volume | Recommended Solution |
|----------|----------------|---------------------|
| Line Chart | < 1,000 points | Direct rendering |
| Line Chart | 1,000 ~ 10,000 points | Downsample to within 500 points |
| Line Chart | > 10,000 points | Backend aggregation + time range filtering |
| Scatter Plot | < 5,000 points | Direct rendering |
| Scatter Plot | 5,000 ~ 50,000 points | Canvas rendering + downsampling |

> **Detailed Documentation**: [Performance Optimization](references/patterns/g2-pattern-performance.md)

### 18.3 Responsive

autoFit adaptive, ResizeObserver dynamic adjustment, mobile font/margin adaptation.

> **Detailed Documentation**: [Responsive Adaptation](references/patterns/g2-pattern-responsive.md)

---