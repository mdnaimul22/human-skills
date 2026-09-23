---
name: "math-animate"
description: "Render mathematical, geometric, and scientific animations into MP4, GIF, WebM, or PNG using Manim Community Edition. Supports LaTeX formulas, 2D/3D shapes, calculus graphing, and transparent overlays."
version: "1.0.0"
author: "Human Skill Team"
tags: ["animation", "graphics", "math", "manim", "visualization", "video", "latex", "geometry"]
trigger_patterns:
  - "math animation"
  - "manim"
  - "render manim"
  - "math video"
  - "animate equation"
  - "calculus animation"
  - "geometry animation"
  - "latex animation"
  - "plot animation"
---

# Mathematical & Scientific Animation (Manim)

## When to Use

Activate this skill when the user asks to:
- Create mathematical animations, geometry transformations, or formula morphs.
- Visualize calculus, coordinate systems, linear algebra, or physics phenomena.
- Generate educational math videos (MP4), WebM overlays, or animated GIF demonstrations.
- Render transparent animations for video compositing or presentations.
- Export single-frame mathematical figures or diagrams to PNG.

## The **math_animate** Tool

This skill uses the `math_animate` tool to compile and render Python Manim scenes into high-quality media files.

### 📝 PARAMETERS:

| Parameter | Type | Required | Default | Description |
|:---|:---|:---:|:---|:---|
| `scene_code` | `string` | **Yes** | — | Python code defining a Manim Scene with a `construct()` method. |
| `scene_name` | `string` | No | *auto-detected* | Name of the Scene class to render (e.g. `"CircleToSquare"`). |
| `output_path` | `string` | No | `manim_<Scene>.<fmt>` | Target filepath for the rendered output. |
| `quality` | `string` | No | `"medium"` | Preset: `"low"` (480p), `"medium"` (720p), `"high"` (1080p), `"4k"` (2160p), `"preview"` (GIF). |
| `format` | `string` | No | `"mp4"` | Output format: `"mp4"`, `"gif"`, `"png"`, `"webm"`. |
| `transparent` | `string` | No | `"false"` | Render with an alpha/transparent background (`"true"` / `"false"`). |
| `background_color` | `string` | No | *default black* | Hex color code for canvas background (e.g. `"#1a1a2e"`). |
| `allow_unsafe_code`| `string` | No | `"false"` | Bypass AST security denylist check (`"true"` / `"false"`). |

### 🎬 QUALITY PRESETS:

| Quality Preset | Resolution | Frame Rate | Intended Use |
|:---|:---|:---|:---|
| `"preview"` | 854x480 | 15 fps | Quick loop preview, compact GIF for README |
| `"low"` | 854x480 | 15 fps | Fast draft rendering during code development |
| `"medium"` | 1280x720 | 30 fps | Standard balance of speed and clarity (Default) |
| `"high"` | 1920x1080 | 60 fps | Crisp Full HD production video |
| `"4k"` | 3840x2160 | 60 fps | Ultra-high definition presentation / master output |

---

## 📋 HOW TO CALL THIS TOOL:

The agent executes `human-skills` with the JSON payload passed directly as a string argument:

```bash
human-skills '{"tool_name": "math_animate", "tool_args": {"scene_code": "class CircleToSquare(Scene):\n    def construct(self):\n        circle = Circle(color=BLUE)\n        square = Square(color=RED)\n        self.play(Create(circle))\n        self.play(Transform(circle, square))\n        self.wait(1)", "scene_name": "CircleToSquare", "quality": "medium", "format": "mp4", "output_path": "output/circle_to_square.mp4"}}'
```

Which maps to this JSON payload:
```json
{
    "tool_name": "math_animate",
    "tool_args": {
        "scene_code":  "class CircleToSquare(Scene):\n    def construct(self):\n        circle = Circle(color=BLUE)\n        square = Square(color=RED)\n        self.play(Create(circle))\n        self.play(Transform(circle, square))\n        self.wait(1)",
        "scene_name":  "CircleToSquare",
        "quality":     "medium",
        "format":      "mp4",
        "output_path": "output/circle_to_square.mp4"
    }
}
```

Expected output:
```
✅ Mathematical Animation Rendered Successfully.
   Output      : /home/user/workdir/output/circle_to_square.mp4
   Scene       : CircleToSquare
   Quality     : medium (1280x720 @ 30fps)
   Format      : mp4
   Size        : 1.2 MB
   Render Time : 4.12s
   Duration    : 3.0s
```

### ⚠️ IMPORTANT NOTES:
- **All values in `tool_args` must be strings** (e.g. `"transparent": "true"`, not `true`).
- **Dependencies**: Requires `manim` CLI (`pip install manim`) and `ffmpeg` (for encoding & probe).
- **Auto Import**: `from manim import *` is automatically injected if not present in `scene_code`.
- **Scene Detection**: If `scene_name` is omitted, the tool automatically detects the `Scene` class.
- **AST Security**: Unsafe imports (`os`, `sys`, `subprocess`, `socket`, `open`, etc.) are blocked by default.

---

## Scenario-Based Instructions

### 📐 Scenario 1: Geometry & LaTeX Equation Transformation

**When:** Morphing geometric figures and displaying mathematical formulas (e.g. Euler's Identity, Pythagorean theorem).

**Example:**
```bash
human-skills '{
    "tool_name": "math_animate",
    "tool_args": {
        "scene_code": "class EulerIdentity(Scene):\n    def construct(self):\n        title = Tex(r\"Euler's Formula\", font_size=48)\n        formula = MathTex(r\"e^{i\pi} + 1 = 0\", font_size=64, color=YELLOW)\n        self.play(Write(title))\n        self.wait(0.5)\n        self.play(title.animate.to_edge(UP))\n        self.play(Write(formula))\n        self.play(Indicate(formula))\n        self.wait(1)",
        "scene_name": "EulerIdentity",
        "quality": "medium",
        "format": "mp4",
        "output_path": "output/euler_identity.mp4"
    }
}'
```

---

### 📈 Scenario 2: Calculus & Coordinate Graphing

**When:** Plotting function curves, coordinate axes, and dynamic tangents (e.g. derivatives, sine waves).

**Example:**
```bash
human-skills '{
    "tool_name": "math_animate",
    "tool_args": {
        "scene_code": "class SineWave(Scene):\n    def construct(self):\n        axes = Axes(x_range=[0, 7, 1], y_range=[-1.5, 1.5, 0.5], x_length=8, y_length=4)\n        labels = axes.get_axis_labels(x_label=\"x\", y_label=\"\\sin(x)\")\n        sine_curve = axes.plot(lambda x: np.sin(x), color=BLUE, x_range=[0, 2*np.pi])\n        self.play(Create(axes), Write(labels))\n        self.play(Create(sine_curve), run_time=2)\n        self.wait(1)",
        "scene_name": "SineWave",
        "quality": "high",
        "format": "mp4",
        "output_path": "output/sine_wave.mp4"
    }
}'
```

---

### 🖼️ Scenario 3: Fast Animated GIF Preview for Documentation / Web

**When:** Creating a quick, lightweight GIF animation for a README, web page, or tutorial.

**Example:**
```bash
human-skills '{
    "tool_name": "math_animate",
    "tool_args": {
        "scene_code": "class PulseDot(Scene):\n    def construct(self):\n        dot = Dot(color=PURPLE, radius=0.3)\n        self.add(dot)\n        self.play(dot.animate.scale(2).set_color(TEAL), rate_func=there_and_back, run_time=1.5)\n        self.wait(0.5)",
        "scene_name": "PulseDot",
        "quality": "preview",
        "format": "gif",
        "output_path": "docs/pulse_dot.gif"
    }
}'
```

---

### 🎭 Scenario 4: Transparent Overlay for Video Editing (WebM / Alpha)

**When:** Rendering motion graphics with a transparent background to composite over live footage or slide decks.

**Example:**
```bash
human-skills '{
    "tool_name": "math_animate",
    "tool_args": {
        "scene_code": "class LowerThird(Scene):\n    def construct(self):\n        banner = Rectangle(width=6.0, height=1.0, color=GOLD, fill_opacity=0.3)\n        text = Text(\"Mathematical Proof\", font_size=32, color=WHITE)\n        group = VGroup(banner, text).to_corner(DL, buff=0.8)\n        self.play(FadeIn(group, shift=RIGHT))\n        self.wait(2)\n        self.play(FadeOut(group, shift=LEFT))",
        "scene_name": "LowerThird",
        "quality": "medium",
        "format": "webm",
        "transparent": "true",
        "output_path": "output/lower_third_overlay.webm"
    }
}'
```

---

### 🧊 Scenario 5: 3D Surface & Camera Motion

**When:** Demonstrating 3D vector fields, surfaces, or rotating perspective geometries using `ThreeDScene`.

**Example:**
```bash
human-skills '{
    "tool_name": "math_animate",
    "tool_args": {
        "scene_code": "class ThreeDSphere(ThreeDScene):\n    def construct(self):\n        axes = ThreeDAxes()\n        sphere = Surface(lambda u, v: np.array([1.5 * np.cos(u) * np.cos(v), 1.5 * np.cos(u) * np.sin(v), 1.5 * np.sin(u)]), u_range=[-np.pi/2, np.pi/2], v_range=[0, 2*np.pi], resolution=(16, 32), fill_color=BLUE_D, fill_opacity=0.7)\n        self.set_camera_orientation(phi=75 * DEGREES, theta=-45 * DEGREES)\n        self.add(axes)\n        self.play(Create(sphere))\n        self.begin_ambient_camera_rotation(rate=0.2)\n        self.wait(2)\n        self.stop_ambient_camera_rotation()",
        "scene_name": "ThreeDSphere",
        "quality": "medium",
        "format": "mp4",
        "output_path": "output/threed_sphere.mp4"
    }
}'
```
