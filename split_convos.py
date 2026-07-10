# usage: python split_convos.py
# access the export file via File -> Settings -> Privacy -> Export data
# you will then need to use Zen browser to access the download link.
import json, re, os, sys
from datetime import datetime

# SRC = "conversations 07.09.26.json"
SRC = "conversations 07.09.26.json"
OUT_DIR = "."

with open(SRC, encoding="utf-8") as f:
    conversations = json.load(f)

def slugify_name(name, max_words=4):
    words = re.findall(r"[A-Za-z0-9']+", name)
    short = "_".join(words[:max_words])
    return short

def fmt_date(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%m.%d.%y")

def tool_use_note(block, out_dir=None):
    name = block.get("name", "tool")
    inp = block.get("input", {}) or {}
    if name == "web_search":
        return f"*? Searched the web: \"{inp.get('query','')}\"*"
    if name == "image_search":
        return f"*? Searched images: \"{inp.get('query','')}\"*"
    if name == "bash_tool":
        cmd = inp.get("command", "")
        return f"*? Ran bash command:*\n```bash\n{cmd}\n```"
    if name == "create_file":
        return f"*? Created file: `{inp.get('path','')}`*"
    if name == "str_replace":
        return f"*? Edited file: `{inp.get('path','')}`*"
    if name == "view":
        return f"*? Viewed: `{inp.get('path','')}`*"
    if name == "present_files":
        paths = inp.get("filepaths", [])
        return f"*? Shared file(s): {', '.join(paths)}*"
    if name == "visualize:show_widget":
        title = inp.get("title", "diagram")
        code = inp.get("widget_code", "")
        if code.strip().startswith("<svg") and out_dir is not None:
            fixed_svg = colorize_svg_tree(code)
            svg_filename = f"{title}.svg"
            svg_path = os.path.join(out_dir, svg_filename)
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(fixed_svg)
            return f"![{title}]({svg_filename})"
        # HTML/interactive widgets can't be flattened to a static image
        return f"*? Generated an interactive visual: \"{title}\" (not recoverable as a static image)*"
    return f"*? Used tool: {name}*"

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg")

# Color ramps used by the Visualizer tool's SVG diagrams (class c-{ramp}).
# These classes normally resolve via a stylesheet injected by claude.ai's
# widget host; once extracted standalone, that stylesheet is gone, so every
# rect/text defaults to black fill. We rebuild the light-mode equivalent here.
RAMPS = {
    "purple": {"50": "#EEEDFE", "600": "#534AB7", "800": "#3C3489", "900": "#26215C"},
    "teal":   {"50": "#E1F5EE", "600": "#0F6E56", "800": "#085041", "900": "#04342C"},
    "coral":  {"50": "#FAECE7", "600": "#993C1D", "800": "#712B13", "900": "#4A1B0C"},
    "pink":   {"50": "#FBEAF0", "600": "#993556", "800": "#72243E", "900": "#4B1528"},
    "gray":   {"50": "#F1EFE8", "600": "#5F5E5A", "800": "#444441", "900": "#2C2C2A"},
    "blue":   {"50": "#E6F1FB", "600": "#185FA5", "800": "#0C447C", "900": "#042C53"},
    "green":  {"50": "#EAF3DE", "600": "#3B6D11", "800": "#27500A", "900": "#173404"},
    "amber":  {"50": "#FAEEDA", "600": "#854F0B", "800": "#633806", "900": "#412402"},
    "red":    {"50": "#FCEBEB", "600": "#A32D2D", "800": "#791F1F", "900": "#501313"},
}

import xml.etree.ElementTree as ET

def colorize_svg_tree(svg_code):
    """Bake ramp colors directly onto elements as fill/stroke/font attributes,
    instead of relying on a <style> block with CSS class selectors. Many SVG
    viewers (e.g. FastStone) only honor presentation attributes and don't
    correctly cascade descendant CSS selectors like '.c-teal .ts' — baking
    the colors in directly guarantees correct rendering everywhere."""
    try:
        root = ET.fromstring(svg_code)
    except ET.ParseError:
        return svg_code  # leave untouched if we can't parse it

    def classes_of(el):
        return (el.get("class") or "").split()

    def walk(el, ramp, in_box):
        classes = classes_of(el)
        tag = el.tag.split("}")[-1]
        for c in classes:
            if c.startswith("c-") and c[2:] in RAMPS:
                ramp = c[2:]
        if "box" in classes:
            in_box = True
        if in_box and tag in ("rect", "circle", "ellipse"):
            el.set("fill", "#fbfaf7")
            el.set("stroke", "#888780")
        elif ramp and tag in ("rect", "circle", "ellipse"):
            stops = RAMPS[ramp]
            el.set("fill", stops["50"])
            el.set("stroke", stops["600"])
        if tag == "text":
            stops = RAMPS.get(ramp)
            if "th" in classes or "t" in classes:
                el.set("fill", stops["800"] if stops else "#222220")
                el.set("font-weight", "bold" if "th" in classes else "normal")
                el.set("font-size", "14px")
            elif "ts" in classes:
                el.set("fill", stops["600"] if stops else "#5f5e5a")
                el.set("font-size", "12px")
            el.set("font-family", "Arial, Helvetica, sans-serif")
        for child in el:
            walk(child, ramp, in_box)

    walk(root, None, False)
    root.set("xmlns", "http://www.w3.org/2000/svg")
    return ET.tostring(root, encoding="unicode")

def render_files_note(files):
    parts = []
    for f in files:
        fname = f.get("file_name", "attached_file")
        if fname.lower().endswith(IMAGE_EXTS):
            parts.append(
                f"![{fname}]({fname})\n\n"
                f"*(Image not included in export — save `{fname}` from claude.ai "
                f"and place it in this same folder for the link above to work.)*"
            )
        else:
            parts.append(f"*? Attached file: `{fname}` (not included in export — save manually if needed)*")
    return "\n\n".join(parts)

def render_content_blocks(blocks, out_dir=None):
    parts = []
    for b in blocks:
        btype = b.get("type")
        if btype == "text":
            txt = b.get("text", "")
            if txt.strip():
                parts.append(txt)
        elif btype == "thinking":
            txt = b.get("thinking") or b.get("text") or ""
            if txt.strip():
                parts.append(
                    "<details>\n<summary>Thinking</summary>\n\n"
                    + txt.strip() +
                    "\n\n</details>"
                )
        elif btype == "tool_use":
            parts.append(tool_use_note(b, out_dir=out_dir))
        elif btype == "tool_result":
            # Skip verbatim tool output (search results, file dumps, etc.)
            # to keep the transcript readable; the assistant's text response
            # already incorporates the relevant findings.
            continue
    return "\n\n".join(parts)

written = []
for conv in conversations:
    name = conv.get("name") or "Untitled conversation"
    created = conv.get("created_at")
    date_str = fmt_date(created) if created else "unknown_date"
    slug = slugify_name(name)
    # filename = f"{slug}_{date_str}.md"
    filename = f"{date_str}_{slug}.md"
    filepath = os.path.join(OUT_DIR, filename)

    lines = [f"# {name}", "", f"*{created[:10] if created else ''}*", ""]

    for msg in conv.get("chat_messages", []):
        sender = msg.get("sender")
        header = "## You" if sender == "human" else "## Claude"
        body = render_content_blocks(msg.get("content", []), out_dir=OUT_DIR)

        files = (msg.get("files") or []) + (msg.get("attachments") or [])
        if files:
            files_note = render_files_note(files)
            body = (body + "\n\n" + files_note).strip() if body.strip() else files_note

        if not body.strip():
            continue
        lines.append(header)
        lines.append("")
        lines.append(body)
        lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    written.append(filepath)

print("\n".join(written))
