import json
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "skills" / "storage" / "my_skills" / "human-skills-tools" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import skills.helpers.paths
from patch_text import PatchText
from skills.helpers.execute import dispatch


def _get_html_fixture(tmp_path: Path) -> Path:
    source = _PROJECT_ROOT / "test" / "ai-1791629104273-518_animation.html"
    target = tmp_path / "animation_test.html"
    shutil.copy(source, target)
    return target


def _build_twelve_chunks() -> list[dict]:
    return [
        {
            "TargetContent": "<title>Neural Data Matrix Network</title>",
            "ReplacementContent": "<title>Hyper Quantum Neural Matrix [Debugged & Patched]</title>",
        },
        {
            "TargetContent": "  html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; background: #030712; }\n  #canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: block; }",
            "ReplacementContent": "  html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; background: #00030a; user-select: none; }\n  #canvas { position: fixed; inset: 0; width: 100%; height: 100%; display: block; filter: contrast(1.15) saturate(1.2); }",
        },
        {
            "TargetContent": "const LOOP_DURATION = 10.0;\nconst LAYERS_CONFIG = [5, 7, 8, 7, 6, 3];\nconst LAYER_COLORS = [",
            "ReplacementContent": "const LOOP_DURATION = 16.0;\nconst LAYERS_CONFIG = [6, 8, 10, 8, 6, 4];\nconst LAYER_PALETTE = [",
        },
        {
            "TargetContent": "  { r: 0, g: 210, b: 255 },   // Cyan\n  { r: 40, g: 150, b: 255 },  // Deep Cyan-Blue\n  { r: 150, g: 80, b: 255 },  // Electric Violet\n  { r: 235, g: 60, b: 220 },  // Neon Magenta\n  { r: 255, g: 110, b: 50 },  // Bright Coral\n  { r: 255, g: 190, b: 40 }   // Gold / Orange",
            "ReplacementContent": "  { r: 0, g: 255, b: 230 },   // Cyber Cyan\n  { r: 0, g: 140, b: 255 },  // Electric Cobalt\n  { r: 140, g: 40, b: 255 },  // Deep Ultraviolet\n  { r: 255, g: 30, b: 180 },  // Hyper Magenta\n  { r: 255, g: 90, b: 30 },   // Plasma Orange\n  { r: 255, g: 215, b: 0 }    // Core Gold",
        },
        {
            "TargetContent": "let width, height, baseDim, cx, cy;\nlet matrixChars = [];\nlet packets = [];",
            "ReplacementContent": "let width, height, baseDim, cx, cy, renderEpoch;\nlet matrixChars = [];\nlet packetStreams = [];\nlet frameCounter = 0;\nlet lastFrameTime = performance.now();\nlet animationState = 'RUNNING';",
        },
        {
            "TargetContent": "  const chars = '0101010101100101ABCDEF';",
            "ReplacementContent": "  const chars = '0110100101010110ABCDEF9876543210';",
        },
        {
            "TargetContent": "  const offsetX = Math.sin(loopPhase * 2 + l * 1.3 + i * 0.7) * baseDim * 0.006;",
            "ReplacementContent": "  const offsetX = Math.sin(loopPhase * 3.0 + l * 1.45 + i * 0.85) * baseDim * 0.0085;",
        },
        {
            "TargetContent": "  const bgGrad = ctx.createRadialGradient(cx, cy, baseDim * 0.1, cx, cy, Math.hypot(width, height) * 0.65);\n  bgGrad.addColorStop(0, '#09152e');\n  bgGrad.addColorStop(0.5, '#050c1e');\n  bgGrad.addColorStop(1, '#02050d');\n  ctx.fillStyle = bgGrad;",
            "ReplacementContent": "  const bgGrad = ctx.createRadialGradient(cx, cy, baseDim * 0.05, cx, cy, Math.hypot(width, height) * 0.7);\n  ctx.fillStyle = bgGrad;",
        },
        {
            "TargetContent": "  // Subtle Tech Matrix Grid\n",
            "ReplacementContent": "",
        },
        {
            "TargetContent": "    const charY = (mc.y - (loopProgress * mc.speed * height)) % height;\n    const finalY = charY < 0 ? charY + height : charY;\n    const pulse = 0.5 + 0.5 * Math.sin(loopProgress * Math.PI * 2 * 3 + mc.phase);",
            "ReplacementContent": "    const charY = (mc.y - (loopProgress * mc.speed * height * 1.35)) % height;\n    const finalY = charY < 0 ? charY + height : charY;\n    const pulse = 0.6 + 0.4 * Math.sin(loopProgress * Math.PI * 6 + mc.phase);",
        },
        {
            "TargetContent": "        ctx.strokeStyle = synGrad;\n        ctx.lineWidth = Math.max(1, baseDim * 0.0018);",
            "ReplacementContent": "        ctx.strokeStyle = synGrad;\n        ctx.lineWidth = Math.max(1.2, baseDim * 0.0024);",
        },
        {
            "TargetContent": "resize();\nrequestAnimationFrame(render);",
            "ReplacementContent": "initAnimationCanvas();\nrequestAnimationFrame(renderLoop);",
        },
    ]


def test_multiline_ten_plus_simultaneous_patches_via_dispatch(tmp_path):
    target = _get_html_fixture(tmp_path)
    chunks = _build_twelve_chunks()

    res = dispatch({
        "tool_name": "patch_text",
        "tool_args": {
            "TargetFile": str(target),
            "ReplacementChunks": json.dumps(chunks),
            "auto_check": "true",
            "strict_mode": "true",
        },
    })

    assert "File updated successfully" in res
    assert "12 chunk(s) applied" in res
    assert "Syntax  : ✓ passed" in res

    patched_content = target.read_text()

    for chunk in chunks:
        assert chunk["TargetContent"] not in patched_content
        if chunk["ReplacementContent"]:
            assert chunk["ReplacementContent"] in patched_content

    assert "<!DOCTYPE html>" in patched_content
    assert "</html>" in patched_content
    assert "animationState = 'RUNNING';" in patched_content
    assert "filter: contrast(1.15) saturate(1.2);" in patched_content
    assert "const LOOP_DURATION = 16.0;" in patched_content


@pytest.mark.asyncio
async def test_multiline_patches_via_tool_class(tmp_path):
    target = _get_html_fixture(tmp_path)
    chunks = _build_twelve_chunks()[:10]

    tool = PatchText(args={
        "TargetFile": str(target),
        "ReplacementChunks": chunks,
        "auto_check": "true",
        "strict_mode": "true",
    })
    res = await tool.execute()

    assert "File updated successfully" in res.message
    assert "10 chunk(s) applied" in res.message
    assert res.additional["chunks_count"] == 10

    patched_content = target.read_text()
    for chunk in chunks:
        assert chunk["TargetContent"] not in patched_content
        if chunk["ReplacementContent"]:
            assert chunk["ReplacementContent"] in patched_content


def test_multiline_shuffled_order_preservation(tmp_path):
    target = _get_html_fixture(tmp_path)
    chunks = _build_twelve_chunks()
    shuffled_chunks = [chunks[11], chunks[0], chunks[8], chunks[2], chunks[5], chunks[10], chunks[1], chunks[7], chunks[4], chunks[6], chunks[3], chunks[9]]

    res = dispatch({
        "tool_name": "patch_text",
        "tool_args": {
            "TargetFile": str(target),
            "ReplacementChunks": json.dumps(shuffled_chunks),
        },
    })

    assert "File updated successfully" in res
    assert "12 chunk(s) applied" in res

    patched_content = target.read_text()
    for chunk in chunks:
        assert chunk["TargetContent"] not in patched_content
        if chunk["ReplacementContent"]:
            assert chunk["ReplacementContent"] in patched_content


def test_multiline_with_explicit_line_bounds(tmp_path):
    target = _get_html_fixture(tmp_path)
    bounded_chunks = [
        {
            "StartLine": 6,
            "EndLine": 6,
            "TargetContent": "<title>Neural Data Matrix Network</title>",
            "ReplacementContent": "<title>Bounded Quantum Matrix</title>",
        },
        {
            "StartLine": 8,
            "EndLine": 9,
            "TargetContent": "  html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; background: #030712; }\n  #canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: block; }",
            "ReplacementContent": "  html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; background: #050510; }\n  #canvas { position: fixed; inset: 0; width: 100%; height: 100%; display: block; }",
        },
        {
            "StartLine": 18,
            "EndLine": 20,
            "TargetContent": "const LOOP_DURATION = 10.0;\nconst LAYERS_CONFIG = [5, 7, 8, 7, 6, 3];\nconst LAYER_COLORS = [",
            "ReplacementContent": "const LOOP_DURATION = 14.0;\nconst LAYERS_CONFIG = [5, 7, 8, 7, 6, 3];\nconst LAYER_COLORS = [",
        },
        {
            "StartLine": 47,
            "EndLine": 47,
            "TargetContent": "  const chars = '0101010101100101ABCDEF';",
            "ReplacementContent": "  const chars = 'ABCDEF1234567890';",
        },
        {
            "StartLine": 96,
            "EndLine": 96,
            "TargetContent": "  const offsetX = Math.sin(loopPhase * 2 + l * 1.3 + i * 0.7) * baseDim * 0.006;",
            "ReplacementContent": "  const offsetX = Math.sin(loopPhase * 2.2 + l * 1.3 + i * 0.7) * baseDim * 0.006;",
        },
        {
            "StartLine": 110,
            "EndLine": 110,
            "TargetContent": "  // Subtle Tech Matrix Grid\n",
            "ReplacementContent": "",
        },
        {
            "StartLine": 179,
            "EndLine": 180,
            "TargetContent": "        ctx.strokeStyle = synGrad;\n        ctx.lineWidth = Math.max(1, baseDim * 0.0018);",
            "ReplacementContent": "        ctx.strokeStyle = synGrad;\n        ctx.lineWidth = Math.max(1.5, baseDim * 0.002);",
        },
        {
            "StartLine": 299,
            "EndLine": 300,
            "TargetContent": "resize();\nrequestAnimationFrame(render);",
            "ReplacementContent": "runCanvasSetup();\nstartAnimationLoop();",
        },
    ]

    res = dispatch({
        "tool_name": "patch_text",
        "tool_args": {
            "TargetFile": str(target),
            "ReplacementChunks": json.dumps(bounded_chunks),
        },
    })

    assert "File updated successfully" in res
    assert "8 chunk(s) applied" in res
    patched = target.read_text()
    assert "<title>Bounded Quantum Matrix</title>" in patched
    assert "ABCDEF1234567890" in patched
    assert "runCanvasSetup();" in patched
    assert "startAnimationLoop();" in patched


def test_multiline_adjacent_consecutive_chunks(tmp_path):
    target = tmp_path / "adjacent.txt"
    target.write_text("line_1\nline_2\nline_3\nline_4\n")

    chunks = [
        {"TargetContent": "line_1\n", "ReplacementContent": "ALPHA_1\n"},
        {"TargetContent": "line_2\n", "ReplacementContent": "BETA_2\n"},
        {"TargetContent": "line_3\n", "ReplacementContent": "GAMMA_3\n"},
    ]

    res = dispatch({
        "tool_name": "patch_text",
        "tool_args": {
            "TargetFile": str(target),
            "ReplacementChunks": json.dumps(chunks),
        },
    })

    assert "File updated successfully" in res
    assert "3 chunk(s) applied" in res
    assert target.read_text() == "ALPHA_1\nBETA_2\nGAMMA_3\nline_4\n"


def test_multiline_contraction_and_expansion_mix(tmp_path):
    target = tmp_path / "mix.txt"
    target.write_text("H1\nH2\nH3\nBODY_A\nBODY_B\nBODY_C\nBODY_D\nBODY_E\nFOOT_1\n")

    chunks = [
        {
            "TargetContent": "H1\nH2\nH3\n",
            "ReplacementContent": "H1\nH2\nH2_SUB\nH2_EXTRA\nH3\n",
        },
        {
            "TargetContent": "BODY_A\nBODY_B\nBODY_C\nBODY_D\nBODY_E\n",
            "ReplacementContent": "BODY_COMPACT\n",
        },
        {
            "TargetContent": "FOOT_1\n",
            "ReplacementContent": "FOOT_EXPANDED_A\nFOOT_EXPANDED_B\n",
        },
    ]

    res = dispatch({
        "tool_name": "patch_text",
        "tool_args": {
            "TargetFile": str(target),
            "ReplacementChunks": json.dumps(chunks),
        },
    })

    assert "File updated successfully" in res
    assert "3 chunk(s) applied" in res
    expected = "H1\nH2\nH2_SUB\nH2_EXTRA\nH3\nBODY_COMPACT\nFOOT_EXPANDED_A\nFOOT_EXPANDED_B\n"
    assert target.read_text() == expected


@pytest.mark.asyncio
async def test_multiline_strict_syntax_rejection_on_html(tmp_path):
    target = _get_html_fixture(tmp_path)
    original_content = target.read_text()

    chunks = [
        {
            "TargetContent": "<title>Neural Data Matrix Network</title>",
            "ReplacementContent": "<title>Valid Title</title>",
        },
        {
            "TargetContent": "<body>",
            "ReplacementContent": "<body><div class='broken' unclosed_tag",
        },
    ]

    tool = PatchText(args={
        "TargetFile": str(target),
        "ReplacementChunks": chunks,
        "auto_check": "true",
        "strict_mode": "true",
    })
    res = await tool.execute()

    assert "Syntax validation failed" in res.message
    assert target.read_text() == original_content


@pytest.mark.asyncio
async def test_multiline_overlapping_chunks_rejection(tmp_path):
    target = tmp_path / "overlap.txt"
    target.write_text("line_1\nline_2\nline_3\nline_4\nline_5\n")

    chunks = [
        {
            "StartLine": 2,
            "EndLine": 4,
            "TargetContent": "line_2\nline_3\nline_4",
            "ReplacementContent": "block_A",
        },
        {
            "StartLine": 3,
            "EndLine": 5,
            "TargetContent": "line_3\nline_4\nline_5",
            "ReplacementContent": "block_B",
        },
    ]

    tool = PatchText(args={
        "TargetFile": str(target),
        "ReplacementChunks": chunks,
    })
    res = await tool.execute()

    assert "Overlapping replacement chunks detected" in res.message


def test_multiline_cli_integration_ten_chunks(tmp_path):
    target = _get_html_fixture(tmp_path)
    chunks = _build_twelve_chunks()[:10]

    payload = json.dumps({
        "tool_name": "patch_text",
        "tool_args": {
            "TargetFile": str(target),
            "ReplacementChunks": json.dumps(chunks),
        },
    })

    run = subprocess.run(
        ["human-skills", payload],
        capture_output=True,
        text=True,
    )

    assert run.returncode == 0
    assert "File updated successfully" in run.stdout
    assert "10 chunk(s) applied" in run.stdout

    patched = target.read_text()
    assert "<title>Hyper Quantum Neural Matrix [Debugged & Patched]</title>" in patched
    assert "const LOOP_DURATION = 16.0;" in patched
    assert "animationState = 'RUNNING';" in patched
