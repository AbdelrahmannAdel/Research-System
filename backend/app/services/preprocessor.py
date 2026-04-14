import re       # regex

# clean raw PDF text for use by classifier and keyword extractor
# removes noise: hyphenated line breaks, extra white space, page numbers
def clean_text(text: str) -> str:
    
    #rejoin words split across line with a hyphen
    text = re.sub(r"-\n", "", text)

    # replace newlines with spaces so text flows as prose
    text = re.sub(r"\n", " ", text)
    
    # remove standalone page numbers
    text = re.sub(r"(?m)^\s*\d{1,4}\s*$", "", text)
    
    # collapse multiple spaces into one and strip leading/trailing whitespace
    text = re.sub(r" +", " ", text).strip()
    
    return text

