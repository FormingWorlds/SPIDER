import re
from pathlib import Path
import bibtexparser

DOCS_DIR = Path("docs")
BIB_FILE = DOCS_DIR / "refs.bib"

CITE_PATTERN = re.compile(r"\[@([A-Za-z0-9:_-]+)([^\]]*)\]")

def clean_tex(s):
    if not s:
        return ""
    return (
        s.replace("{", "")
         .replace("}", "")
         .replace("~", " ")
         .replace("\\&", "&")
         .strip()
    )

def format_authors(author_field):
    if not author_field:
        return ""
    authors = [clean_tex(a.strip()) for a in author_field.split(" and ")]
    return "; ".join(authors)

def format_entry(entry):
    authors = format_authors(entry.get("author", ""))
    title = clean_tex(entry.get("title", "Untitled"))
    year = clean_tex(entry.get("year", "n.d."))
    journal = clean_tex(
        entry.get("journal") or entry.get("booktitle") or entry.get("publisher") or ""
    )
    address = clean_tex(entry.get("address", ""))

    parts = [authors, f"*{title}*", journal, address, year]
    return ", ".join(p for p in parts if p) + "."

with open(BIB_FILE, "r", encoding="utf-8") as f:
    bib_db = bibtexparser.load(f)

bib_map = {e["ID"]: format_entry(e) for e in bib_db.entries if "ID" in e}

for md_file in DOCS_DIR.rglob("*.md"):
    text = md_file.read_text(encoding="utf-8")

    # Skip files that do not contain raw citation syntax.
    if not CITE_PATTERN.search(text):
        print(f"Skipped {md_file} (no [@...] citations found)")
        continue

    used = {}

    def repl(match):
        key = match.group(1)
        suffix = match.group(2).strip()
        used[key] = bib_map.get(key, f"Missing bibliography entry for {key}.")
        if suffix:
            return f"[^cite-{key}], {suffix}"
        return f"[^cite-{key}]"

    new_text = CITE_PATTERN.sub(repl, text)

    if used:
        footnotes = "\n".join(
            f"[^cite-{key}]: {value}" for key, value in used.items()
        )

        # Remove an existing \bibliography line if present
        new_text = re.sub(r"(?m)^\s*\\bibliography\s*$\n?", "", new_text)

        # Remove any old generated cite footnotes before appending fresh ones
        new_text = re.sub(
            r"(?m)^\[\^cite-[A-Za-z0-9:_-]+\]:\s.*(?:\n(?!\[\^cite-).*)*",
            "",
            new_text
        ).rstrip()

        new_text += "\n\n" + footnotes + "\n"

    md_file.write_text(new_text, encoding="utf-8")
    print(f"Processed {md_file}")