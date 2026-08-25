"""Brand mention detection.

The naive approach -- `"modal" in text.lower()` -- produces false positives on
"multimodal", "modality", and "modal window", and matches the ordinary English
word "together". This module compiles per-brand patterns instead, and records
*where* the first mention lands so we can rank brands within a single answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable, Optional, List
from urllib.parse import urlparse


@dataclass
class Brand:
    key: str
    label: str
    patterns: List[str] = field(default_factory=list)
    case_sensitive_patterns: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    is_us: bool = False

    def compiled(self):
        out = [re.compile(p, re.IGNORECASE) for p in self.patterns]
        out += [re.compile(p) for p in self.case_sensitive_patterns]
        return out


@dataclass
class Mention:
    brand: str
    label: str
    mentioned: bool
    count: int
    first_index: Optional[int]
    rank: Optional[int]
    cited: bool
    matched_text: Optional[str]

    def as_row(self):
        return asdict(self)


def load_brands(cfg: dict):
    return [Brand(**b) for b in cfg["brands"]]


def _domain_of(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return ""
    if not host:
        host = url.strip().lower()
    return host[4:] if host.startswith("www.") else host


def detect(text: str, brands: Iterable[Brand], citations: Iterable[str] = ()):
    """Return one Mention per brand, ranked by first appearance in `text`."""
    text = text or ""
    cited_domains = {_domain_of(u) for u in citations}
    results = []

    for brand in brands:
        hits = []
        for pattern in brand.compiled():
            hits.extend(pattern.finditer(text))

        cited = any(
            d == bd or d.endswith("." + bd)
            for d in cited_domains
            for bd in brand.domains
        )

        if hits:
            first = min(hits, key=lambda m: m.start())
            results.append(Mention(
                brand=brand.key,
                label=brand.label,
                mentioned=True,
                count=len({(m.start(), m.end()) for m in hits}),
                first_index=first.start(),
                rank=None,
                cited=cited,
                matched_text=first.group(0),
            ))
        else:
            results.append(Mention(
                brand=brand.key,
                label=brand.label,
                mentioned=False,
                count=0,
                first_index=None,
                rank=None,
                cited=cited,
                matched_text=None,
            ))

    present = sorted([m for m in results if m.mentioned], key=lambda m: m.first_index)
    for i, m in enumerate(present, start=1):
        m.rank = i

    return results
