import re
import fitz  # PyMuPDF

def extract_from_pdf(file_bytes: bytes) -> dict:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_text = [page.get_text() for page in doc]
    full_text = "\n".join(pages_text)

    title = _extract_title(doc, pages_text)

    abstract = _extract_section(
        full_text,
        start_keywords=["abstract"],
        end_keywords=["introduction", "keywords", "index terms", "1.", "1 "]
    )

    intro = _extract_section(
        full_text,
        start_keywords=["introduction", "1. introduction", "1 introduction"],
        end_keywords=["2.", "2 ", "related work", "background", "methodology", "preliminaries"]
    )

    if abstract and len(abstract.split()) >= 150:
        summary_input = abstract
    elif abstract and intro:
        summary_input = abstract + "\n\n" + intro
    elif abstract:
        summary_input = abstract
    elif intro:
        summary_input = intro
    else:
        words = full_text.split()
        summary_input = " ".join(words[:2000])

    doc.close()

    return {
        "title": title,
        "abstract": abstract,
        "intro": intro,
        "full_text": full_text,
        "summary_input": summary_input,
    }

def _extract_title(doc, pages_text: list) -> str:
    title = doc.metadata.get("title", "").strip()
    if title and len(title) > 5:
        return title

    first_page_lines = []
    for line in pages_text[0].splitlines():
        if line.strip():
            first_page_lines.append(line.strip())

    for line in first_page_lines[:15]:
        if len(line) < 10:
            continue
        if line.isupper():
            continue
        if re.match(r"^\d{4}$", line):
            continue
        return line

    return first_page_lines[0] if first_page_lines else "Unknown Title"

def _extract_section(text: str, start_keywords: list, end_keywords: list) -> str:
    text_lower = text.lower()

    start_pos = None
    for keyword in start_keywords:
        # Pattern 1: standalone heading line
        pattern_standalone = rf"(?m)^\s*{re.escape(keyword)}\s*$"
        match = re.search(pattern_standalone, text_lower)
        if match:
            start_pos = match.end()
            break

        # Pattern 2: heading followed by em-dash or period then content
        # e.g. "Abstract—This paper..." or "Abstract. This paper..."
        pattern_inline = rf"(?m)^\s*{re.escape(keyword)}[\s\-—–.:]+(.+)"
        match = re.search(pattern_inline, text_lower)
        if match:
            start_pos = match.start(1)
            break

        # Pattern 3: numbered heading e.g. "I. Introduction" or "1. Introduction"
        pattern_numbered = rf"(?m)^\s*(?:[IVXivx]+\.|[\d]+\.)\s*{re.escape(keyword)}\s*$"
        match = re.search(pattern_numbered, text_lower)
        if match:
            start_pos = match.end()
            break

    if start_pos is None:
        return ""

    # Find earliest end keyword
    end_pos = len(text)
    for keyword in end_keywords:
        pattern = rf"(?m)^\s*{re.escape(keyword)}[\s\S]{{0,50}}$"
        match = re.search(pattern, text_lower[start_pos:])
        if match:
            candidate = start_pos + match.start()
            if candidate < end_pos:
                end_pos = candidate

    extracted = text[start_pos:end_pos].strip()

    # Strip trailing metadata noise
    noise_patterns = [
        r'\[\s*[Cc]ode\s*\].*$',
        r'\d+\s*[A-Z][a-z]+\s+University.*$',
        r'[Cc]orrespondence\s+to:.*$',
        r'[Pp]roceedings\s+of.*$',
        r'[Cc]opyright\s+\d{4}.*$',
        r'[Ee]qual\s+contribution.*$',
        r'\*\s*[Ee]qual.*$',
    ]

    for pattern in noise_patterns:
        extracted = re.sub(pattern, '', extracted, flags=re.DOTALL).strip()

    # Strip structured abstract section headers (PubMed/clinical trial format)
    extracted = re.sub(
        r'\b(OBJECTIVE|DESIGN|SETTING|PARTICIPANTS|INTERVENTION|METHODS|RESULTS|CONCLUSIONS?|BACKGROUND|PURPOSE|AIMS?|TRIAL REGISTRATION)[:\s]*\n?',
        ' ',
        extracted
    )
    extracted = re.sub(r' +', ' ', extracted).strip()

    return extracted