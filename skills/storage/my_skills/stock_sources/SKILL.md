---
name: "stock_sources"
description: "High-resolution stock media collector for Pixabay and Pexels. Supports engagement-based popularity ranking, aspect ratio filtering (horizontal, vertical, square), video duration bounds, Pexels avg_color palette extraction, and autonomous manifest.json generation."
version: "1.0.0"
author: "Human Skills Team"
tags: ["stock", "media", "pexels", "pixabay", "video", "image", "manifest", "popularity", "collector"]
trigger_patterns:
  - "stock_sources"
  - "stock collector"
  - "download stock"
  - "pexels"
  - "pixabay"
  - "stock videos"
  - "stock images"
---

# stock_sources — Unified Stock Media Collector & Manifest Engine

> *"Collect high-fidelity stock videos and images from Pixabay and Pexels with engagement ranking, aspect ratio precision, color palette extraction, and automated manifest tracking."*

---

## Overview

`stock_sources` is an autonomous media collection engine that queries leading stock platforms (**Pixabay**, **Pexels**, and **Archive.org**), ranks assets using empirical engagement statistics, filters by precise aspect ratios and duration, extracts dominant color palettes, and arranges downloads into cleanly categorized folders accompanied by a structured `manifest.json`.

---

## Key Features

1. **Popularity & Quality Scoring**:
   - **Pixabay Engagement Formula**: `(likes * 3.0) + (downloads * 1.5) + (views * 0.05)` prioritizes proven, community-validated media.
   - **Pexels Resolution & Quality Metric**: Ranks assets based on pixel density (`width * height`) and video frame rate (`fps`).
   - **Archive.org Historical Archival**: Access to public domain documentary films, newsreels, and historical clips with download popularity metrics.
2. **Aspect Ratio Precision**:
   - **`horizontal`**: Wide formats (16:9, 16:10, 21:9) with width-to-height ratio $\ge 1.35$.
   - **`vertical`**: Portrait formats (9:16, 4:5) with ratio $\le 0.85$ (optimized for YouTube Shorts, Reels, TikTok).
   - **`square`**: 1:1 format ($0.85 < \text{ratio} < 1.35$).
3. **Pexels `avg_color` Palette Extraction**:
   - Extracts the primary HEX color code for every image and allows color-scoped queries (e.g. `orange`, `blue`, `turquoise`).
4. **Duration Bounds**:
   - Fine-tune video clips with `min_duration` and `max_duration` in seconds.
5. **Autonomous `manifest.json` Generation**:
   - Automatically generates a machine-readable manifest documenting file paths, resolutions, aspect ratios, durations, sizes, tags, creator info, and engagement scores.
6. **Concurrent High-Speed Streaming**:
   - Multi-threaded chunked downloads (`ThreadPoolExecutor`) with network stream buffers preventing memory overhead.

---

## Tool Reference: `stock_collector`

### 📝 Arguments

| Argument | Type | Default | Required | Description |
|:---|:---:|:---:|:---:|:---|
| `query` | `string` | — | **Yes** | Search keyword or prompt (e.g. `"cyberpunk city"`, `"ocean waves"`). |
| `sources` | `string` | `"all"` | No | Stock providers to query: `"all"`, `"pixabay"`, `"pexels"`, or `"pixabay,pexels"`. |
| `video_count` | `integer` | `2` | No | Number of videos to download per provider. |
| `image_count` | `integer` | `2` | No | Number of images to download per provider. |
| `aspect_ratio` | `string` | `null` | No | Target aspect ratio: `"horizontal"`, `"vertical"`, or `"square"`. |
| `min_duration` | `integer` | `null` | No | Minimum video duration in seconds. |
| `max_duration` | `integer` | `null` | No | Maximum video duration in seconds. |
| `color` | `string` | `null` | No | Color theme filter (e.g. `"orange"`, `"blue"`, `"black"`, `"white"`). |
| `output_dir` | `string` | `"downloads"` | No | Target base directory for downloads and manifest. |
| `concurrent_downloads` | `integer` | `6` | No | Maximum number of concurrent download worker threads. |

---

## Output Directory Structure

Each collection run organizes downloaded media and its manifest as follows:

```
<output_dir>/<query>/
├── videos/
│   ├── video_140111.mp4
│   └── video_38697718.mp4
├── images/
│   ├── image_1751455.jpg
│   └── image_33926926.jpeg
└── manifest.json
```

---

## Manifest Schema Reference (`manifest.json`)

The generated manifest provides structured metadata:

```json
{
  "query": "ocean",
  "providers": ["pixabay", "pexels"],
  "total_items": 4,
  "total_videos": 2,
  "total_images": 2,
  "items": [
    {
      "file_name": "video_140111.mp4",
      "file_path": "downloads/ocean/videos/video_140111.mp4",
      "kind": "video",
      "source_id": "140111",
      "resolution": "3840x2160",
      "aspect_ratio": "horizontal",
      "duration_seconds": 20.0,
      "file_size_bytes": 45802437,
      "file_size_mb": 43.68,
      "creator": "Natures_Embrace",
      "page_url": "https://pixabay.com/videos/id-140111/",
      "download_url": "https://cdn.pixabay.com/video/...",
      "views": 1083777,
      "downloads": 651338,
      "likes": 6781,
      "popularity_score": 1051538.85,
      "tags": "sea, ocean, seagulls, sunset",
      "provider": "pixabay"
    },
    {
      "file_name": "image_33926926.jpeg",
      "file_path": "downloads/ocean/images/image_33926926.jpeg",
      "kind": "image",
      "source_id": "33926926",
      "resolution": "5005x2815",
      "aspect_ratio": "horizontal",
      "duration_seconds": 0.0,
      "file_size_bytes": 230807,
      "file_size_mb": 0.22,
      "creator": "Ákos Solymár",
      "page_url": "https://www.pexels.com/...",
      "download_url": "https://images.pexels.com/...",
      "avg_color": "#919D99",
      "quality_score": 14.09,
      "tags": "Beautiful sunset over water...",
      "provider": "pexels"
    }
  ]
}
```

---

## Usage Examples

### 1. Collect Multi-Source 4K Horizontal Media
```bash
human-skills '{
  "tool_name": "stock_collector",
  "tool_args": {
    "query": "aurora borealis",
    "sources": "all",
    "aspect_ratio": "horizontal",
    "video_count": 1,
    "image_count": 1,
    "output_dir": "data/stock_library"
  }
}'
```

### 2. Collect Vertical Videos for Shorts & Reels
```bash
human-skills '{
  "tool_name": "stock_collector",
  "tool_args": {
    "query": "street food",
    "sources": "pexels",
    "aspect_ratio": "vertical",
    "video_count": 3,
    "image_count": 0,
    "min_duration": 5,
    "max_duration": 30,
    "output_dir": "data/vertical_reels"
  }
}'
```

### 3. Collect Images with Pexels Color Palette
```bash
human-skills '{
  "tool_name": "stock_collector",
  "tool_args": {
    "query": "desert dunes",
    "sources": "pexels",
    "color": "orange",
    "video_count": 0,
    "image_count": 4,
    "output_dir": "data/dune_palette"
  }
}'
```
