import sys, unicodedata, re
sys.path.insert(0, '.')
from app.services.pdf_extractor import extract_from_pdf

with open('C:/users/hp/Desktop/papers to test/CCCCCC.pdf', 'rb') as f:
    file_bytes = f.read()

extracted = extract_from_pdf(file_bytes)

abstract = extracted['abstract'] or extracted['intro'] or extracted['summary_input']
abstract = unicodedata.normalize('NFKC', abstract)
abstract = re.sub(r'-\n', '', abstract)
abstract = re.sub(r'\n', ' ', abstract)
title = unicodedata.normalize('NFKC', extracted['title'] or '')

print('=== TITLE ===')
print(repr(title))

print()
print('=== ABSTRACT (raw repr) ===')
print(repr(abstract))

print()
print('=== ABSTRACT (readable) ===')
print(abstract)
