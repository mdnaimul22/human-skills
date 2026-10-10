import json
from helpers.tool import Tool, Response
from helpers.files import exists, is_dir, read_text, write_text
from helpers.validator import validate_syntax, CheckResult


def _count_lines(text: str) -> int:
    return text.count("\n") + (1 if text and not text.endswith("\n") else 0)


def _apply_bounded_replace(
    content: str,
    target_content: str,
    replacement_content: str,
    start_line: int | None,
    end_line: int | None,
    allow_multiple: bool,
) -> tuple[str, int, int]:
    lines = content.splitlines(keepends=True)
    total_lines = len(lines)
    s_idx = max((start_line - 1), 0) if start_line is not None else 0
    e_idx = min(end_line, total_lines) if end_line is not None else total_lines
    if s_idx > total_lines:
        raise ValueError(f"StartLine ({start_line}) exceeds file line count ({total_lines})")
    if s_idx > e_idx:
        raise ValueError(f"StartLine ({start_line}) cannot be greater than EndLine ({end_line})")

    prefix = "".join(lines[:s_idx])
    slice_text = "".join(lines[s_idx:e_idx])
    suffix = "".join(lines[e_idx:])

    count = slice_text.count(target_content)
    if count == 0:
        if start_line is not None or end_line is not None:
            raise ValueError(f"TargetContent not found between lines {start_line or 1} and {end_line or total_lines}")
        raise ValueError("TargetContent not found in file")
    if count > 1 and not allow_multiple:
        raise ValueError(f"TargetContent matched {count} times between lines {start_line or 1} and {end_line or total_lines}; specify a tighter range or set AllowMultiple=true")

    replaced_slice = slice_text.replace(target_content, replacement_content) if allow_multiple else slice_text.replace(target_content, replacement_content, 1)
    new_content = prefix + replaced_slice + suffix

    first_match_offset = slice_text.index(target_content)
    match_line_from = (prefix + slice_text[:first_match_offset]).count("\n") + 1
    nl_count = target_content.count("\n")
    if target_content.endswith("\n"):
        nl_count = max(nl_count - 1, 0)
    match_line_to = match_line_from + nl_count
    return new_content, match_line_from, match_line_to


def _parse_chunk(raw: dict) -> dict:
    target = raw.get("TargetContent") or raw.get("target_content") or raw.get("old_text") or ""
    replacement = raw.get("ReplacementContent")
    if replacement is None:
        replacement = raw.get("replacement_content")
    if replacement is None:
        replacement = raw.get("new_text")
    if replacement is None:
        replacement = ""

    start_raw = raw.get("StartLine") if raw.get("StartLine") is not None else raw.get("start_line")
    end_raw = raw.get("EndLine") if raw.get("EndLine") is not None else raw.get("end_line")
    start_line = int(start_raw) if start_raw is not None and str(start_raw).strip() != "" else None
    end_line = int(end_raw) if end_raw is not None and str(end_raw).strip() != "" else None

    allow_raw = raw.get("AllowMultiple") if raw.get("AllowMultiple") is not None else raw.get("allow_multiple", False)
    allow_multiple = str(allow_raw).lower() in ("true", "1", "yes")

    return {
        "target_content": str(target),
        "replacement_content": str(replacement),
        "start_line": start_line,
        "end_line": end_line,
        "allow_multiple": allow_multiple,
    }


class PatchText(Tool):
    name = "patch_text"
    description = "Precisely replace content or chunks in an existing file with line bounds, single/multi chunk edits, and syntax validation."
    arguments = {
        "TargetFile": "Absolute path to the target file to edit. (REQUIRED, alias: target_file, path)",
        "TargetContent": "The exact string to be replaced for a single edit. (alias: old_text, target_content)",
        "ReplacementContent": "The content to replace TargetContent with. Default: empty string. (alias: new_text, replacement_content)",
        "StartLine": "1-based starting line number to search within. Optional. (alias: start_line)",
        "EndLine": "1-based ending line number to search within. Optional. (alias: end_line)",
        "AllowMultiple": "If true, replace all occurrences of TargetContent in range. Default: false. (alias: allow_multiple)",
        "ReplacementChunks": "Array of chunk objects for non-contiguous multi-edits: [{TargetContent, ReplacementContent, StartLine, EndLine, AllowMultiple}]. (alias: replacement_chunks, chunks)",
        "auto_check": "Validate syntax before saving. Default: true.",
        "strict_mode": "Block file modification on syntax errors. Default: false.",
    }
    instruction = "For skill instructions run: human-skills --skill_info human-skills-tools"

    async def execute(self, **kwargs) -> Response:
        target_file = (
            self.args.get("TargetFile")
            or self.args.get("target_file")
            or self.args.get("path")
            or self.args.get("file_path")
            or ""
        ).strip()

        if not target_file:
            return Response(
                message="❌ Error: 'TargetFile' is required.\n"
                        "Example: human-skills '{\"tool_name\": \"patch_text\", \"tool_args\": {\"TargetFile\": \"/path/to/file.py\", \"TargetContent\": \"old\", \"ReplacementContent\": \"new\"}}'",
                break_loop=False,
            )

        if not exists(target_file):
            return Response(message=f"❌ Error: File not found: '{target_file}'", break_loop=False)

        if is_dir(target_file):
            return Response(message=f"❌ Error: '{target_file}' is a directory, not a file.", break_loop=False)

        chunks_raw = (
            self.args.get("ReplacementChunks")
            or self.args.get("replacement_chunks")
            or self.args.get("chunks")
        )
        if isinstance(chunks_raw, str) and chunks_raw.strip():
            try:
                chunks_raw = json.loads(chunks_raw)
            except json.JSONDecodeError as e:
                return Response(message=f"❌ Error: 'ReplacementChunks' must be valid JSON: {e}", break_loop=False)

        parsed_chunks: list[dict] = []
        if chunks_raw is not None:
            if not isinstance(chunks_raw, list) or len(chunks_raw) == 0:
                return Response(message="❌ Error: 'ReplacementChunks' must be a non-empty list of chunk objects.", break_loop=False)
            for i, c in enumerate(chunks_raw):
                if not isinstance(c, dict):
                    return Response(message=f"❌ Error: Chunk index {i} must be an object.", break_loop=False)
                parsed_c = _parse_chunk(c)
                if not parsed_c["target_content"]:
                    return Response(message=f"❌ Error: Chunk index {i} is missing 'TargetContent'.", break_loop=False)
                parsed_chunks.append(parsed_c)
        else:
            single = _parse_chunk(self.args)
            if not single["target_content"]:
                return Response(
                    message="❌ Error: Either 'TargetContent' (for single edit) or 'ReplacementChunks' (for multi edits) must be provided.",
                    break_loop=False,
                )
            parsed_chunks.append(single)

        try:
            original_content = read_text(target_file)
        except Exception as e:
            return Response(message=f"❌ Error reading file: {e}", break_loop=False)

        for chunk in parsed_chunks:
            if chunk["start_line"] is None:
                if chunk["target_content"] not in original_content:
                    return Response(message=f"❌ Error: TargetContent not found in file: {chunk['target_content'][:60]}", break_loop=False)
                idx = original_content.index(chunk["target_content"])
                chunk["start_line"] = original_content[:idx].count("\n") + 1
            if chunk["end_line"] is None:
                nl_count = chunk["target_content"].count("\n")
                if chunk["target_content"].endswith("\n"):
                    nl_count = max(nl_count - 1, 0)
                chunk["end_line"] = chunk["start_line"] + nl_count

        if len(parsed_chunks) > 1:
            sorted_by_line = sorted(parsed_chunks, key=lambda c: (c["start_line"] or 0))
            for i in range(len(sorted_by_line) - 1):
                cur_end = sorted_by_line[i]["end_line"] or sorted_by_line[i]["start_line"] or 0
                next_start = sorted_by_line[i + 1]["start_line"] or 0
                if cur_end >= next_start:
                    return Response(
                        message=f"❌ Error: Overlapping replacement chunks detected between line {sorted_by_line[i]['start_line']} and line {next_start}.",
                        break_loop=False,
                    )

        descending_chunks = sorted(parsed_chunks, key=lambda c: (c["start_line"] or 0), reverse=True)
        current_content = original_content
        touched_ranges: list[tuple[int, int]] = []

        try:
            for chunk in descending_chunks:
                current_content, l_from, l_to = _apply_bounded_replace(
                    current_content,
                    chunk["target_content"],
                    chunk["replacement_content"],
                    chunk["start_line"],
                    chunk["end_line"],
                    chunk["allow_multiple"],
                )
                touched_ranges.append((l_from, l_to))
        except ValueError as e:
            return Response(message=f"❌ Error applying replacement: {e}", break_loop=False)

        auto_check = str(self.args.get("auto_check", "true")).lower() not in ("false", "0", "no")
        strict_mode = str(self.args.get("strict_mode", "false")).lower() in ("true", "1", "yes")

        check_result: CheckResult | None = None
        if auto_check and current_content.strip():
            check_result = validate_syntax(current_content, target_file)
            if strict_mode and not check_result.valid:
                error_lines = ["❌ Syntax validation failed — file NOT modified.", ""]
                error_lines += [f"  × {err}" for err in check_result.errors]
                if check_result.warnings:
                    error_lines += [""] + [f"  ! {w}" for w in check_result.warnings]
                error_lines.append("\n🔧 Fix the syntax errors in your replacement and retry.")
                return Response(message="\n".join(error_lines), break_loop=False)

        try:
            write_text(target_file, current_content)
        except Exception as e:
            return Response(message=f"❌ Error writing patched file: {e}", break_loop=False)

        total_lines = _count_lines(current_content)
        size = len(current_content.encode("utf-8"))
        size_s = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
        ranges_s = ", ".join(f"L{f}-L{t}" for f, t in sorted(touched_ranges, key=lambda r: r[0]))

        lines = [
            f"✅ File updated successfully: {target_file}",
            f"   Chunks  : {len(parsed_chunks)} chunk(s) applied ({ranges_s})",
            f"   Lines   : {total_lines}",
            f"   Size    : {size_s}",
        ]
        if check_result:
            lines.append("   Syntax  : ✓ passed" if check_result.valid else "   Syntax  : ⚠️  warnings (file modified anyway)")
            if check_result.warnings:
                for w in check_result.warnings:
                    lines.append(f"   ! {w}")
            if not check_result.valid and check_result.errors:
                for err in check_result.errors:
                    lines.append(f"   × {err}")

        return Response(
            message="\n".join(lines),
            break_loop=False,
            additional={
                "path": target_file,
                "chunks_count": len(parsed_chunks),
                "total_lines": total_lines,
                "size_bytes": size,
            },
        )
