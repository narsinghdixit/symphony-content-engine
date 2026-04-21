#!/usr/bin/env python3
"""Convert /inbox files (.docx, .pdf) to markdown for agent processing."""
import sys
from pathlib import Path

INBOX = Path(__file__).parent / "inbox"
SUPPORTED = {".docx", ".pdf", ".md", ".txt"}


def docx_to_md(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = para.style.name if para.style else ""
        if style.startswith("Heading"):
            level = style[-1] if style[-1].isdigit() else "2"
            lines.append(f"{'#' * int(level)} {text}")
        else:
            lines.append(text)
    return "\n\n".join(lines)


def pdf_to_md(path: Path) -> str:
    import pdfplumber

    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n---\n\n".join(pages)


def passthrough(path: Path) -> str:
    return path.read_text(encoding="utf-8")


CONVERTERS = {
    ".docx": docx_to_md,
    ".pdf": pdf_to_md,
    ".md": passthrough,
    ".txt": passthrough,
}


def main():
    files = sorted(
        f for f in INBOX.iterdir()
        if f.suffix.lower() in SUPPORTED and not f.name.startswith(".")
    )
    if not files:
        print("No processable files in /inbox/")
        sys.exit(0)
    for src in files:
        if src.suffix.lower() in (".md", ".txt"):
            print(f"  passthrough: {src.name}")
            continue
        out = INBOX / f"{src.stem}.md"
        text = CONVERTERS[src.suffix.lower()](src)
        out.write_text(f"# {src.stem}\n\n{text}", encoding="utf-8")
        print(f"  converted: {src.name} -> {out.name} ({len(text):,} chars)")
    print("Ingestion complete.")


if __name__ == "__main__":
    main()
