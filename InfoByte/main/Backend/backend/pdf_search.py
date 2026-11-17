"""Search local textbooks. Page numbers refer to the PDF, starting at one."""
import logging
import re
from functools import lru_cache
from unicodedata import normalize

from pypdf import PdfReader


def clean(text):
    return " ".join(normalize("NFC", text).split())


@lru_cache(maxsize=64)
def read_pages(path, modified, size):
    # Modification time and size distinguish versions of the same book.
    with path.open("rb") as stream:
        reader = PdfReader(stream)
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            paragraphs = re.split(r"\n\s*\n", text)
            pages.append(tuple(clean(p) for p in paragraphs if p.strip()))
        return tuple(pages)


def passages(paragraph, pattern):
    sentences = re.split(r"(?<=[.!?…])\s+", paragraph)
    first = None
    for sentence in sentences:
        hit = pattern.search(sentence)
        if hit is None:
            continue
        definition = bool(re.match(r"\s*(?:[—–−-]|дегеніміз\b)", sentence[hit.end():], re.I)
                          or re.search(r"\bдеп\s+аталады\b", sentence, re.I))
        excerpt = paragraph if len(paragraph) <= 360 else sentence
        match = pattern.search(excerpt)
        item = (excerpt[:match.start()], match.group(), excerpt[match.end():])
        if definition:
            return True, item
        if first is None:
            first = item
    if first:
        return False, first


def search_collection(directory, term):
    pattern = re.compile(re.escape(clean(term)), re.I)
    files = sorted((p for p in directory.glob("*") if p.suffix.lower() == ".pdf"
                    and p.is_file() and not p.is_symlink()), key=lambda p: (p.name.casefold(), p.name))
    results, skipped, seen = [], [], set()
    for path in files:
        try:
            stat = path.stat()
            pages = read_pages(path, stat.st_mtime_ns, stat.st_size)
        except Exception:
            logging.getLogger(__name__).warning("Cannot read %s", path.name, exc_info=True)
            skipped.append(path.name)
            continue
        if not any(pages):
            skipped.append(path.name)
            continue
        preferred, other = [], []
        local_keys = set()
        remaining = 10 - len(results)
        for number, paragraphs in enumerate(pages, 1):
            for paragraph in paragraphs:
                found = passages(paragraph, pattern)
                if not found:
                    continue
                definition, parts = found
                key = "".join(parts).casefold()
                bucket = preferred if definition else other
                if key in seen or key in local_keys or len(bucket) >= remaining:
                    continue
                before, match, after = parts
                bucket.append((key, dict(book=path.name, page=number,
                                         before=before, match=match, after=after)))
                local_keys.add(key)
                if len(preferred) == remaining:
                    break
            if len(preferred) == remaining:
                break
        for key, result in (preferred + other)[:remaining]:
            seen.add(key)
            results.append(result)
        if len(results) == 10:
            break
    notice = "" if files else "Кітапхана бос. books қалтасына PDF кітап қосыңыз."
    if skipped:
        notice = "Кітаптың мәтінін оқу мүмкін болмады: " + ", ".join(skipped)
    return {"results": results, "notice": notice}

