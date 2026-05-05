

---
name: chart-visualization
description: Visualize data as charts. Call this skill when users need to generate bar charts, line charts, pie charts, scatter plots, radar charts, Sankey diagrams, mind maps, flowcharts, etc., to generate chart images by calling AntV API via curl tool.
---

Please visualize data as charts based on user input.
## Steps
1. Analyze user data and requirements, select the most suitable chart type
2. Construct a compliant JSON request body
3. Use curl tool to call API to generate chart image
4. Output the returned image URL in Markdown image format
## Chart Selection Guide
Based on user data characteristics and requirements, select the most suitable chart type:
- **Time Series**: Use `line` (trend) or `area` (cumulative trend); two different dimensions use `dual-axes`
- **Comparison**: Use `bar` (horizontal category comparison) or `column` (vertical category comparison); frequency distribution use `histogram`
- **Proportion**: Use `pie` (proportion composition) or `treemap` (hierarchical proportion)
- **Relationship & Flow**: Use `scatter` (correlation), `sankey` (flow) or `venn` (set overlap)
- **Hierarchy & Tree**: Use `organization-chart` or `mind-map`
- **Special Types**:
  - `radar`: Multi-dimensional comparison
  - `funnel`: Process stage conversion
  - `liquid`: Percentage/Progress
  - `word-cloud`: Text word frequency
  - `boxplot` / `violin`: Statistical distribution
  - `network-graph`: Complex node relationships
  - `fishbone-diagram`: Causal analysis
  - `flow-diagram`: Flowchart
  - `spreadsheet`: Structured data table or pivot table
## API Interface
POST https://antv-studio.alipay.com/api/gpt-vis
Request body is JSON, must include `type` and `source: "chart-visualization-skills"` fields.
Example:
```bash
curl -X POST https://antv-studio.alipay.com/api/gpt-vis \
-H "Content-Type: application/json" \
-d '{"type":"line","source":"chart-visualization-skills","data":[{"time":"2025-01","value":100}],"title":"Example Chart"}'
```
Return Example:
```json
{"success":true,"resultObj":"https://..."}
```
Output the URL in `resultObj` in Markdown image format: `![Chart](URL)`
## Supported Chart Types
| Category | Chart Type |
|------|---------|
| Comparison | Bar Chart(bar), Column Chart(column), Waterfall Chart(waterfall), Dual Axes Chart(dual-axes) |
| Trend | Area Chart(area), Line Chart(line), Scatter Plot(scatter) |
| Distribution | Box Plot(boxplot), Histogram(histogram), Violin Plot(violin), Funnel Chart(funnel) |
| Proportion | Pie Chart(pie), Liquid Chart(liquid), Word Cloud(word-cloud) |
| Hierarchy | Organization Chart(organization-chart), Mind Map(mind-map), Treemap(treemap), Sankey Diagram(sankey) |
| Relationship | Network Graph(network-graph), Venn Diagram(venn) |
| Process | Flow Diagram(flow-diagram), Fishbone Diagram(fishbone-diagram) |
| Multi-dimensional | Radar Chart(radar) |
| Table | Table/Pivot Table(spreadsheet) |
## General Optional Parameters
| Parameter | Type | Default | Description |
|------|------|--------|------|
| theme | string | "default" | Theme: "default" / "academy" / "dark" |
| width | number | 600 | Chart width |
| height | number | 400 | Chart height |
| title | string | "" | Chart title |
| style.texture | string | "default" | Texture: "default" / "rough" (hand-drawn style) |
Charts with axes also support: axisXTitle, axisYTitle.
## Data Formats for Each Chart
- **area / line**: `{time: string, value: number, group?: string}[]`, optional stack: boolean
- **bar**: `{category: string, value: number, group?: string}[]`, optional group / stack (default stack: true)
- **column**: `{category: string, value: number, group?: string}[]`, optional group (default true) / stack
- **scatter**: `{x: number, y: number, group?: string}[]`
- **pie**: `{category: string, value: number}[]`, optional innerRadius: number (0-1)
- **radar**: `{name: string, value: number, group?: string}[]`
- **funnel**: `{category: string, value: number}[]`
- **waterfall**: `{category: string, value?: number, isTotal?: boolean, isIntermediateTotal?: boolean}[]`
- **dual-axes**: categories: string[], series: {type: "column"|"line", data: number[], axisYTitle?: string}[]
- **histogram**: `number[]`, optional binNumber: number
- **boxplot / violin**: `{category: string, value: number, group?: string}[]`
- **liquid**: percent: number (0-1), optional shape: "circle"|"rect"|"pin"|"triangle"
- **word-cloud**: `{text: string, value: number}[]`
- **sankey**: `{source: string, target: string, value: number}[]`, optional nodeAlign
- **treemap**: `{name: string, value: number, children?: ...}[]` (max 3 levels deep)
- **venn**: `{sets: string[], value: number, label?: string}[]`
- **network-graph / flow-diagram**: `{nodes: {name: string}[], edges: {source: string, target: string, name?: string}[]}`
- **fishbone-diagram / mind-map**: `{name: string, children?: ...}` (max 3 levels deep)
- **organization-chart**: `{name: string, description?: string, children?: ...}` (max 3 levels deep), optional orient: "horizontal"|"vertical"
- **spreadsheet**: `Record<string, string | number>[]`, optional rows / columns / values (pivot table fields)