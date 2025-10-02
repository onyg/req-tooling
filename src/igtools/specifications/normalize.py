import re
import json
import hashlib
import html
from typing import Dict, List, Tuple

ZERO_WIDTH = (
    "\u200B"  # zero width space
    "\u200C"  # zero width non-joiner
    "\u200D"  # zero width joiner
    "\uFEFF"  # zero width no-break space (BOM)
)
ZW_RE = re.compile(f"[{ZERO_WIDTH}]")

NBSP_RE = re.compile(r"\u00A0")  # non-breaking space
SOFT_HYPHEN_RE = re.compile(r"\u00AD")

# Remove <actor>...</actor> blocks (keep everything else as-is)
ACTOR_BLOCK_RE = re.compile(r"<actor\b[^>]*?>.*?</actor>", re.IGNORECASE | re.DOTALL)

# Remove generic HTML tags but keep their inner text (no BeautifulSoup to avoid reformatting)
TAG_RE = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>", re.DOTALL)

def normalize_text_for_semantics(raw: str) -> str:
    """
    Make editorial changes vanish while preserving meaningful wording.
    - remove actor blocks (they are handled structurally)
    - strip non-rendered characters (ZWSP, BOM)
    - unescape HTML entities (&amp; -> &)
    - remove soft hyphens & NBSP
    - remove tags but keep inner text
    - collapse whitespace runs to single spaces
    - trim
    """
    if not raw:
        return ""
    s = ACTOR_BLOCK_RE.sub("", raw)
    s = html.unescape(s)
    s = SOFT_HYPHEN_RE.sub("", s)
    s = NBSP_RE.sub(" ", s)
    s = ZW_RE.sub("", s)
    s = TAG_RE.sub("", s)
    s = re.sub(r"[ \t\f\r\v]+", " ", s)                     # collapse horizontal whitespace
    s = re.sub(r"\s*\n\s*", " ", s)                         # collapse newlines to spaces
    s = re.sub(r"\s{2,}", " ", s)                           # collapse leftover multi-spaces
    s = s.replace("\r\n", "\n").replace("\r", "\n")         # 1) Newlines vereinheitlichen
    s = s.strip(" ")                                        # 2) Nur normale Spaces am Anfang/Ende entfernen (keine anderen Whitespaces)
    s = re.sub(r" {2,}", " ", s)                            # 3) Doppelte/mehrfache Spaces im Text zu einem Space machen
    s = re.sub(r'\s+', '', s)
    return s.strip().lower()

def canonicalize_actors(actors: List[str]) -> List[str]:
    return sorted({a.strip() for a in (actors or []) if a and a.strip()})

def canonicalize_test_procs(tp_map: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Normalize mapping: actor -> unique sorted list of test IDs.
    Order of actors does not matter.
    """
    canon = {}
    for actor, ids in (tp_map or {}).items():
        if not actor:
            continue
        uniq = sorted({(i or "").strip() for i in ids if i and i.strip()})
        canon[actor.strip()] = uniq
    # Sort keys deterministically by rebuilding dict
    return {k: canon[k] for k in sorted(canon.keys())}


def build_fingerprint(text, title, conformance, actors, test_procedures) -> Tuple[str, dict]:
    canon = {
        "text": normalize_text_for_semantics(text),
        "conformance": (conformance or "").strip(),
        "actors": canonicalize_actors(actors or []),
        "test_procedures": canonicalize_test_procs(test_procedures or {}),
        "title": (title or "").strip(),
    }
    # Stable JSON for hashing
    payload = json.dumps(canon, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return h, canon


def build_requirement_fingerprint(req) -> Tuple[str, dict]:
    """
    req must expose:
      - req.text (raw inner HTML/text including actors markup)
      - req.conformance (e.g., SHALL/SHOULD/MAY)
      - req.actors (list[str])  # optional if you read from YAML
      - req.test_procedures (dict[str, list[str]])  # actor -> [ids]
      - req.title (optional, policy-dependent)
    Returns (hexhash, canonical_dict) for debugging.
    """
    return build_fingerprint(text=getattr(req, "text", ""),
                             title=req.title,
                             conformance=req.conformance,
                             actors=req.actor,
                             test_procedures=getattr(req, "test_procedures", {}))

def is_substantive_change(old_fp: str, new_fp: str) -> bool:
    return old_fp != new_fp


def build_fingerprint_release(requirements) -> str:
    data = []
    for r in sorted(requirements, key=lambda x: x.key):
        data.append({
            "version": r.version,
            "key": r.key,
            "hash": r.content_hash
        })
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
