import sys, re
from collections import defaultdict
import bibtexparser
from pylatexenc.latex2text import LatexNodes2Text

SELF_FAMILY = "Tsutsumi"

def latex2txt(s: str) -> str:
    if not s:
        return ""
    return LatexNodes2Text().latex_to_text(s).strip()

def norm(s: str) -> str:
    return latex2txt(s or "").replace("\n"," ").strip()

def fmt_authors(author_field: str) -> str:
    names = [a.strip() for a in author_field.split(" and ") if a.strip()]
    out = []
    for n in names:
        t = norm(n)
        if "," in t:
            last, first = [x.strip() for x in t.split(",", 1)]
            disp = f"{first} {last}".strip()
        else:
            disp = t
        parts = disp.split()
        if len(parts) >= 2:
            firsts, last = parts[:-1], parts[-1]
            initials = " ".join([p[0]+"." for p in firsts if p])
            disp = f"{initials} {last}"
        if SELF_FAMILY.lower() in disp.lower():
            disp = f"**{disp}**"
        out.append(disp)
    return ", ".join(out)

def md_link_from_doi_or_url(entry):
    doi = (entry.get("doi") or "").strip()
    url = (entry.get("url") or "").strip()
    if doi:
        doi = doi.replace("DOI:", "").replace("doi:", "").strip()
        if not doi.lower().startswith("http"):
            return f"https://doi.org/{doi}"
        return doi
    if url:
        return url
    return ""

def clean_title(title: str) -> str:
    t = norm(title)
    t = re.sub(r"\s+\.", ".", t)
    return t

def venue_line(e):
    j = norm(e.get("journal") or e.get("booktitle") or "")
    vol = norm(e.get("volume"))
    num = norm(e.get("number"))
    pages = norm(e.get("pages"))
    year = norm(e.get("year"))
    parts = []
    if j: parts.append(f"*{j}*")
    if vol: parts.append(vol if not vol.isdigit() else f"**{vol}**")
    if num: parts.append(f"({num})")
    if pages: parts.append(pages)
    if year: parts.append(f"({year})")
    return ", ".join([p for p in parts if p])

def entry_to_markdown(e):
    title = clean_title(e.get("title",""))
    authors = fmt_authors(e.get("author","")) if e.get("author") else ""
    link = md_link_from_doi_or_url(e)
    venue = venue_line(e)

    lines = []
    first = f"- {authors}."
    if title:
        lines.append(first + f' "{title}".')
    else:
        lines.append(first)
    if venue:
        lines.append(f"  {venue}.")
    if link:
        lines.append(f"  [{link}]({link})")
    return "\n".join(lines)

def year_of(e):
    y = (e.get("year") or "").strip()
    m = re.search(r"\d{4}", y)
    return int(m.group()) if m else 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/bib2md.py data/pubs.bib [> content/publications/_index.md]")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        db = bibtexparser.load(f)

    buckets = defaultdict(list)
    for e in db.entries:
        buckets[year_of(e)].append(e)

    years = sorted([y for y in buckets.keys() if y > 0], reverse=True)

    out = []
    out.append("---")
    out.append('title: "Publications"')
    out.append("draft: false")
    out.append("---\n")

    for y in years:
        out.append(f"## {y}")
        for e in sorted(buckets[y], key=lambda x: clean_title(x.get('title','')).lower()):
            out.append(entry_to_markdown(e))
            out.append("")
        out.append("")

    print("\n".join(out).strip() + "\n")

if __name__ == "__main__":
    main()
