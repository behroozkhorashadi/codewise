"""Convert reference_summaries.md to a print-ready HTML file."""

import re
import sys
from pathlib import Path

CSS = """
body {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 13pt;
    line-height: 1.7;
    max-width: 820px;
    margin: 40px auto;
    padding: 0 40px;
    color: #111;
}
h1 { font-size: 20pt; border-bottom: 2px solid #333; padding-bottom: 8px; margin-top: 40px; }
h2 { font-size: 16pt; color: #222; margin-top: 36px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
h3 { font-size: 13pt; color: #333; margin-top: 28px; }
blockquote {
    border-left: 4px solid #999;
    margin: 12px 0 12px 0;
    padding: 4px 16px;
    color: #444;
    font-style: italic;
    background: #f9f9f9;
}
strong { color: #000; }
hr { border: none; border-top: 1px solid #ddd; margin: 28px 0; }
p { margin: 8px 0; }
em { color: #333; }
@media print {
    body { margin: 0; padding: 20px 40px; max-width: 100%; font-size: 11pt; }
    h2 { page-break-before: auto; }
    h3 { page-break-after: avoid; }
    blockquote { page-break-inside: avoid; }
}
"""


def md_to_html(md: str) -> str:
    lines = md.split("\n")
    out = []
    in_blockquote = False

    for line in lines:
        # blockquote (must check before other patterns)
        if line.startswith("> "):
            if not in_blockquote:
                out.append("<blockquote>")
                in_blockquote = True
            content = line[2:]
            content = inline(content)
            out.append(f"<p>{content}</p>")
            continue
        else:
            if in_blockquote:
                out.append("</blockquote>")
                in_blockquote = False

        # headings
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.strip() == "---":
            out.append("<hr>")
        elif line.strip() == "":
            out.append("")
        else:
            out.append(f"<p>{inline(line)}</p>")

    if in_blockquote:
        out.append("</blockquote>")

    return "\n".join(out)


def inline(text: str) -> str:
    # bold+italic ***text***
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    # bold **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # italic *text*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # inline code `text`
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def main():
    src = Path(__file__).parent / "reference_summaries.md"
    dst = Path(__file__).parent / "reference_summaries.html"

    md = src.read_text(encoding="utf-8")
    body = md_to_html(md)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Reference Summaries — Khorashadi Master's Thesis</title>
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>"""

    dst.write_text(html, encoding="utf-8")
    print(f"Written to: {dst}")
    print("Open that file in your browser, then press Cmd+P → Save as PDF.")


if __name__ == "__main__":
    main()
