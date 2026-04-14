import re
import fitz  # PyMuPDF

# Extract text and structure from a research paper PDF
# returns dict with keys: title, abstract, intro, full_text, summary_input
def extract_from_pdf(file_bytes: bytes) -> dict:
    
    # open the pdf from raw bytes in memory, not from a file path
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    
    # loop through every page and extract its text as a list of strings
    pages_text = [page.get_text() for page in doc]
    
    # join all pages into one big string
    full_text = "\n".join(pages_text)
    
    # call _extract_title to extract title
    title = _extract_title(doc, pages_text)
    
    # call _extract_section to extract abstract (giving it where to start and where to end)
    abstract = _extract_section(
        full_text,
        start_keywords=["abstract"],
        end_keywords=["introduction", "keywords", "index terms", "1.", "1 "]
    )
    
    # call _extract_section to extract introduction (giving it where to start and where to end)
    intro = _extract_section(
        full_text,
        start_keywords=["introduction", "1. introduction", "1 introduction"],
        end_keywords=["2.", "2 ", "related work", "background", "methodology", "preliminaries"]
    )

    # hybrid strategy: decide what to send to LLM summarizer
    if abstract and len(abstract.split()) >= 150:   # if the abstract is long enough on its own: just use that
        summary_input = abstract
    elif abstract and intro:                        # abstract is short: combine it with the intro for more context
        summary_input = abstract + "\n\n" + intro
    elif abstract:                                  # abstract found but short, no intro detected: use abstract alone anyway
        summary_input = abstract
    elif intro:                                     # no abstract found at all but intro exists: use that
        summary_input = intro
    else:                                           # nothing detected: fall back to the first 2000 words of raw text
        words = full_text.split()
        summary_input = " ".join(words[:2000])

    # close the doc
    doc.close()

    # return everything as a dict so other services can pick what they need
    return {
        "title": title,
        "abstract": abstract,
        "intro": intro,
        "full_text": full_text,
        "summary_input": summary_input,
    }
    
# extract title helper function
def _extract_title(doc, pages_text: list) -> str:
    
    # check PDF metadata
    title = doc.metadata.get("title", "").strip()
    if title and len(title) > 5:
        return title
    
    # scan the first page line by line, skip empty lines
    first_page_lines = []
    for line in pages_text[0].splitlines():
        if line.strip():    # skip empty lines
            first_page_lines.append(line.strip())
    
    # check each line. skip headers, short lines, and year
    for line in first_page_lines[:15]:
        if len(line) < 10:
            continue
        if line.isupper():
            continue
        if re.match(r"^\d{4}$", line):
            continue
        return line
    
    # last resort return whatever the first line is
    return first_page_lines[0] if first_page_lines else "Unknown Title"

# extract section helper function
def _extract_section(text: str, start_keywords: list, end_keywords: list) -> str:
    
    # lowercase copy for matching
    text_lower = text.lower()
    
    # search for the start keyword as a standalone heading line
    start_pos = None
    for keyword in start_keywords:
        for variant in [keyword, keyword.upper()]:
            pattern = rf"(?m)^\s*{re.escape(variant)}\s*$"
            match = re.search(pattern, text_lower if variant == keyword else text)
            if match:
                start_pos = match.end()
                break
        if start_pos is not None:
            break
    
    # section heading not found
    if start_pos is None:
        return ""
    
    # find earliest end keyword heading
    end_pos = len(text)
    for keyword in end_keywords:
        pattern = rf"(?m)^\s*{re.escape(keyword)}[\s\S]{{0,50}}$"
        match = re.search(pattern, text_lower[start_pos:])
        if match:
            candidate = start_pos + match.start()
            if candidate < end_pos:
                end_pos = candidate     # keep earliest match
                
    return text[start_pos:end_pos].strip()
    