# usage: python split_convos.py
import json, re, os
from datetime import datetime

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

def tool_use_note(block):
    name = block.get("name", "tool")
    inp = block.get("input", {}) or {}
    if name == "web_search":
        return f"*🔧 Searched the web: \"{inp.get('query','')}\"*"
    if name == "image_search":
        return f"*🔧 Searched images: \"{inp.get('query','')}\"*"
    if name == "bash_tool":
        cmd = inp.get("command", "")
        return f"*🔧 Ran bash command:*\n```bash\n{cmd}\n```"
    if name == "create_file":
        return f"*🔧 Created file: `{inp.get('path','')}`*"
    if name == "str_replace":
        return f"*🔧 Edited file: `{inp.get('path','')}`*"
    if name == "view":
        return f"*🔧 Viewed: `{inp.get('path','')}`*"
    if name == "present_files":
        paths = inp.get("filepaths", [])
        return f"*🔧 Shared file(s): {', '.join(paths)}*"
    return f"*🔧 Used tool: {name}*"

def render_content_blocks(blocks):
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
            parts.append(tool_use_note(b))
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
        body = render_content_blocks(msg.get("content", []))
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