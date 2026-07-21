"""
Script parser service.

Owned by: Data Science Lead
Responsibility: Parse Arabic and English script files into structured scene breakdowns.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path


@dataclass
class Scene:
    """Represents a single scene extracted from a script."""

    index: int
    heading: str
    description: str
    characters: list[str] = field(default_factory=list)
    location: str = ""
    time_of_day: str = ""
    mood: str = ""
    dialogue: list[str] = field(default_factory=list)
    language: str = "en"  # 'en' or 'ar'


@dataclass
class ParsedScript:
    """The full structured output of script parsing."""

    title: str
    language: str
    scene_count: int
    scenes: list[Scene] = field(default_factory=list)
    characters: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Arabic Unicode ranges used for script detection
# ---------------------------------------------------------------------------
_ARABIC_RANGES: tuple[tuple[int, int], ...] = (
    (0x0600, 0x06FF),   # Arabic
    (0x0750, 0x077F),   # Arabic Supplement
    (0x08A0, 0x08FF),   # Arabic Extended-A
    (0xFB50, 0xFDFF),   # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),   # Arabic Presentation Forms-B
)

# ---------------------------------------------------------------------------
# Known transition lines (must never become character cues)
# ---------------------------------------------------------------------------
_TRANSITIONS: frozenset[str] = frozenset(
    [
        "CUT TO:",
        "CUT TO",
        "SMASH CUT:",
        "SMASH CUT TO:",
        "MATCH CUT:",
        "MATCH CUT TO:",
        "DISSOLVE TO:",
        "FADE IN:",
        "FADE OUT:",
        "FADE TO BLACK:",
        "FADE TO:",
        "IRIS IN:",
        "IRIS OUT:",
        "THE END",
        "TITLE:",
        "SUPER:",
        "TITLE CARD:",
    ]
)

# ---------------------------------------------------------------------------
# Mood keyword tables
# ---------------------------------------------------------------------------
_MOOD_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "en": {
        "dark": [
            "death", "dead", "blood", "fear", "shadow", "kill", "murder",
            "grave", "corpse", "horror", "scream", "terror", "nightmare",
            "skull", "died", "dying",
        ],
        "tense": [
            "chase", "gun", "danger", "threat", "alarm", "fight", "run",
            "escape", "urgent", "hurry", "trap", "shot", "bullet", "cornered",
            "ambush", "warning",
        ],
        "romantic": [
            "love", "kiss", "heart", "embrace", "together", "darling",
            "passion", "tender", "romantic", "affection", "hold", "gaze",
            "beautiful", "adore",
        ],
    },
    "ar": {
        "dark": [
            "موت", "دم", "خوف", "ظل", "قتل", "جثة", "رعب", "صرخة", "كابوس",
        ],
        "tense": [
            "مطاردة", "خطر", "تهديد", "إنذار", "هرب", "مسدس", "رصاصة",
        ],
        "romantic": [
            "حب", "قبلة", "قلب", "عناق", "معاً", "حبيبي", "حبيبتي", "شغف",
        ],
    },
}

# Precedence for tie-breaking: higher index wins
_MOOD_PRECEDENCE: list[str] = ["neutral", "romantic", "tense", "dark"]


class ScriptParser:
    """
    Parse film scripts (Arabic and English) into structured scene data.

    Usage:
        parser = ScriptParser()
        result = await parser.parse(file_bytes, filename="script.pdf")
    """

    # Compiled once at class level
    _HEADING_RE: re.Pattern = re.compile(
        r"^\s*"
        r"(?:"
        # English tokens
        r"INT\./EXT\.|INT/EXT\.|I/E\.|INT\.|EXT\."
        r"|"
        # Arabic tokens
        r"(?:داخلي|خارجي)[.:]?"
        r")",
        re.IGNORECASE,
    )

    # Parenthetical suffixes on character cue lines
    _PARENTHETICAL_RE: re.Pattern = re.compile(
        r"\s*\((?:V\.O\.|O\.S\.|O\.C\.|CONT'D|CONT'D|voice over|off screen)\)",
        re.IGNORECASE,
    )

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedScript:
        """
        Parse a script file and return structured scene data.

        Args:
            file_bytes: Raw (decrypted) file content
            filename: Original filename (used to detect format)

        Returns:
            ParsedScript with scene breakdown
        """
        ext = Path(filename).suffix.lower()
        text = self._extract_text(file_bytes, ext)
        self._validate_text(text)

        script_language = self._detect_language(text)
        title = self._derive_title(filename)

        lines = text.splitlines()
        scene_pairs = self._split_into_scenes(lines)

        scenes: list[Scene] = []
        seen_characters: dict[str, str] = {}   # lower → original casing
        seen_locations: dict[str, str] = {}    # lower → original casing

        for idx, (heading, body_lines) in enumerate(scene_pairs):
            scene = self._parse_scene(idx, heading, body_lines, script_language)
            scenes.append(scene)

            for char in scene.characters:
                key = char.lower()
                if key not in seen_characters:
                    seen_characters[key] = char

            if scene.location:
                key = scene.location.lower()
                if key not in seen_locations:
                    seen_locations[key] = scene.location

        return ParsedScript(
            title=title,
            language=script_language,
            scene_count=len(scenes),
            scenes=scenes,
            characters=list(seen_characters.values()),
            locations=list(seen_locations.values()),
        )

    # ---------------------------------------------------------------------------
    # Text extraction
    # ---------------------------------------------------------------------------

    def _extract_text(self, file_bytes: bytes, ext: str) -> str:
        """Dispatch to the appropriate extractor based on file extension."""
        if ext == ".txt":
            return self._extract_txt(file_bytes)
        if ext == ".pdf":
            return self._extract_pdf(file_bytes)
        if ext == ".docx":
            return self._extract_docx(file_bytes)
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            "Supported formats are .txt, .pdf, and .docx."
        )

    def _extract_txt(self, file_bytes: bytes) -> str:
        """Decode TXT bytes as UTF-8-SIG then UTF-8. No latin-1 fallback."""
        for encoding in ("utf-8-sig", "utf-8"):
            try:
                return file_bytes.decode(encoding)
            except (UnicodeDecodeError, ValueError):
                continue
        raise ValueError(
            "TXT file is not valid UTF-8. "
            "Only UTF-8 (with or without BOM) is supported."
        )

    def _extract_pdf(self, file_bytes: bytes) -> str:
        """Extract text from a PDF using pypdf."""
        try:
            import pypdf  # noqa: PLC0415

            reader = pypdf.PdfReader(BytesIO(file_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)
        except Exception as exc:
            raise ValueError(f"Could not read PDF: {exc}") from exc

        if not text.strip():
            raise ValueError(
                "PDF contains no extractable text (possibly a scanned image PDF)."
            )
        return text

    def _extract_docx(self, file_bytes: bytes) -> str:
        """Extract text from a DOCX using python-docx."""
        try:
            import docx  # noqa: PLC0415

            doc = docx.Document(BytesIO(file_bytes))
            text = "\n".join(p.text for p in doc.paragraphs)
        except Exception as exc:
            raise ValueError(f"Could not read DOCX: {exc}") from exc

        if not text.strip():
            raise ValueError("DOCX contains no extractable text.")
        return text

    def _validate_text(self, text: str) -> None:
        """Raise ValueError if the extracted text is empty or blank."""
        if not text.strip():
            raise ValueError("Script is empty or contains no meaningful text.")

    # ---------------------------------------------------------------------------
    # Language detection
    # ---------------------------------------------------------------------------

    def _detect_language(self, text: str) -> str:
        """
        Detect whether the script is primarily Arabic, English, or mixed.

        Only Unicode letter characters are counted; digits, punctuation,
        whitespace, and combining marks are ignored.

        Thresholds (Arabic fraction of all letters):
          > 0.60  → 'ar'
          < 0.15  → 'en'
          else    → 'mixed'
        """
        arabic_count = 0
        total_letters = 0

        for ch in text:
            cat = unicodedata.category(ch)
            if not cat.startswith("L"):
                continue
            total_letters += 1
            cp = ord(ch)
            if any(lo <= cp <= hi for lo, hi in _ARABIC_RANGES):
                arabic_count += 1

        if total_letters == 0:
            return "en"

        ratio = arabic_count / total_letters
        if ratio > 0.60:
            return "ar"
        if ratio < 0.15:
            return "en"
        return "mixed"

    # ---------------------------------------------------------------------------
    # Scene segmentation
    # ---------------------------------------------------------------------------

    def _is_scene_heading(self, line: str) -> bool:
        """Return True if the line looks like a screenplay scene heading."""
        return bool(self._HEADING_RE.match(line))

    def _split_into_scenes(
        self, lines: list[str]
    ) -> list[tuple[str, list[str]]]:
        """
        Split a list of lines into (heading, body_lines) pairs.

        Lines before the first valid heading are preamble and are discarded.
        If no heading is found, return one fallback scene with heading="".
        """
        scenes: list[tuple[str, list[str]]] = []
        current_heading: str | None = None
        current_body: list[str] = []

        for line in lines:
            if self._is_scene_heading(line):
                if current_heading is not None:
                    scenes.append((current_heading, current_body))
                # Preamble (before first heading): current_heading is None → discarded
                current_heading = line.strip()
                current_body = []
            else:
                if current_heading is not None:
                    current_body.append(line)
                # else: still in preamble — discard

        # Flush the last scene
        if current_heading is not None:
            scenes.append((current_heading, current_body))

        # No headings found → one fallback scene
        if not scenes:
            return [("", lines)]

        return scenes

    # ---------------------------------------------------------------------------
    # Per-scene parsing
    # ---------------------------------------------------------------------------

    def _parse_scene(
        self,
        index: int,
        heading: str,
        body_lines: list[str],
        script_language: str,
    ) -> Scene:
        """Build a Scene from a heading and its body lines."""
        location, time_of_day = self._extract_location_time(heading)

        # Per-scene language from body text (falls back to script_language)
        body_text = "\n".join(body_lines)
        scene_language = (
            self._detect_language(body_text) if body_text.strip() else script_language
        )

        char_indices = self._extract_characters(body_lines, scene_language)
        dialogue_pairs = self._extract_dialogue(body_lines, char_indices)

        # dialogue_pairs: (char_idx, [text_lines], {source_indices})
        # Use the actual consumed source indices — never reconstruct by arithmetic.
        dialogue_line_set: set[int] = set()
        raw_dialogue: list[str] = []
        for char_idx, dlg_lines, consumed_indices in dialogue_pairs:
            dialogue_line_set |= consumed_indices
            raw_dialogue.extend(dlg_lines)

        characters = [body_lines[i].strip() for i in char_indices]
        # Strip parentheticals from stored character names
        characters = [self._PARENTHETICAL_RE.sub("", c).strip() for c in characters]

        description = self._extract_description(
            body_lines, set(char_indices), dialogue_line_set
        )
        mood = self._extract_mood(body_text, scene_language)

        return Scene(
            index=index,
            heading=heading,
            description=description,
            characters=characters,
            location=location,
            time_of_day=time_of_day,
            mood=mood,
            dialogue=raw_dialogue,
            language=scene_language,
        )

    # ---------------------------------------------------------------------------
    # Field extractors
    # ---------------------------------------------------------------------------

    def _extract_location_time(self, heading: str) -> tuple[str, str]:
        """
        Parse location and time_of_day from a scene heading.

        For 'INT. BAKERY - DAY' → ('BAKERY', 'DAY').
        Returns ('', '') when the heading has no recognisable structure.
        """
        if not heading:
            return ("", "")

        # Strip the leading INT./EXT./etc. or Arabic prefix token
        # Match the prefix token
        m = self._HEADING_RE.match(heading)
        if not m:
            return ("", "")

        remainder = heading[m.end():].strip(" .")

        # Split on ' - ' or ' – ' (em-dash variant)
        for sep in (" - ", " – ", "-"):
            if sep in remainder:
                parts = remainder.split(sep, 1)
                location = parts[0].strip().upper()
                time_of_day = parts[1].strip().upper() if len(parts) > 1 else ""
                return (location, time_of_day)

        # No separator: everything is the location
        return (remainder.strip().upper(), "")

    def _is_transition(self, line: str) -> bool:
        """Return True if the stripped line is a known screenplay transition."""
        return line.strip().upper() in _TRANSITIONS

    def _extract_characters(
        self, body_lines: list[str], language: str
    ) -> list[int]:
        """
        Return indices of character-cue lines in body_lines.

        English: ALL-CAPS, ≤ 6 words, ASCII letters/spaces/hyphens only
                 (after stripping standard parentheticals).
                 Excludes headings, transitions, and known action keywords.

        Arabic:  Passes _is_arabic_character_cue AND has a plausible
                 dialogue line immediately following (structural context rule).
                 The next non-blank line must exist, not be a scene heading,
                 not be a transition, and not itself be another candidate cue.
                 This is a deterministic structural rule — no semantic inference.
        """
        indices: list[int] = []
        for i, raw_line in enumerate(body_lines):
            line = raw_line.strip()
            if not line:
                continue
            if self._is_scene_heading(raw_line):
                continue
            if self._is_transition(line):
                continue

            if language in ("en", "mixed"):
                if self._is_english_character_cue(line):
                    indices.append(i)
            if language in ("ar", "mixed"):
                if self._is_arabic_character_cue(line):
                    if self._has_following_dialogue(body_lines, i):
                        if i not in indices:
                            indices.append(i)

        return sorted(indices)

    def _is_english_character_cue(self, line: str) -> bool:
        """Deterministic check for an English character-cue line."""
        # Strip parentheticals before checking
        clean = self._PARENTHETICAL_RE.sub("", line).strip()
        if not clean:
            return False
        # Must be ALL-CAPS
        if clean != clean.upper():
            return False
        # Only ASCII letters, spaces, hyphens, apostrophes
        if not re.match(r"^[A-Z][A-Z\s\-']*$", clean):
            return False
        # ≤ 6 words
        words = clean.split()
        if len(words) > 6:
            return False
        # Exclude known all-caps action / title keywords
        if clean.rstrip(":") in _TRANSITIONS:
            return False
        return True

    def _is_arabic_character_cue(self, line: str) -> bool:
        """
        Deterministic syntactic check for an Arabic character-cue line.

        Rules (all must hold — purely character-class / structural, no semantics):
          1. Line contains only Arabic-script code points and whitespace
             (no Latin letters, no digits, no punctuation except Arabic punctuation).
          2. ≤ 3 whitespace-separated tokens (tighter than prose action lines).
          3. Does not start with a scene-heading token (داخلي / خارجي).
          4. No Latin letter is present anywhere in the line.
          5. Does not end with Arabic sentence-terminating punctuation (. ، ؟ !)
             that indicates it is a prose/action line rather than a cue.

        Callers must additionally verify structural context via
        _has_following_dialogue before accepting the candidate.
        """
        if not line:
            return False
        # Rule 4: no Latin letters
        if re.search(r"[A-Za-z]", line):
            return False
        # Rule 3: must not start with heading tokens
        if re.match(r"^\s*(?:داخلي|خارجي)", line):
            return False
        # Rule 5: prose lines typically end with sentence-ending punctuation
        if re.search(r"[.،؟!؛]$", line.strip()):
            return False
        # Rule 1 + 2: every non-space character must be Arabic-script; ≤ 3 tokens
        tokens = line.split()
        if not tokens:
            return False
        if len(tokens) > 3:
            return False
        for token in tokens:
            for ch in token:
                cp = ord(ch)
                # Allow Arabic-script letters and a minimal set of Arabic punctuation
                # that can legitimately appear in a name; reject everything else.
                if not any(lo <= cp <= hi for lo, hi in _ARABIC_RANGES) and \
                        ch not in "\u200c\u200d":
                    return False
        return True

    def _has_following_dialogue(self, body_lines: list[str], cue_idx: int) -> bool:
        """
        Structural context check: return True when the line at cue_idx is
        followed by at least one non-blank line that is neither a scene heading,
        a transition, nor itself a bare Arabic-script cue candidate.

        This distinguishes a character cue (which precedes spoken lines) from
        an isolated action/description line that happens to be short.
        """
        for j in range(cue_idx + 1, len(body_lines)):
            candidate = body_lines[j].strip()
            if not candidate:
                continue  # skip blank lines
            # A following scene heading means no dialogue block here
            if self._is_scene_heading(body_lines[j]):
                return False
            if self._is_transition(candidate):
                return False
            # A line that itself looks like an Arabic cue candidate is not
            # dialogue content — it would mean back-to-back cues with nothing
            # between them; treat as no dialogue present.
            if self._is_arabic_character_cue(candidate):
                return False
            # We found a plausible dialogue/action line following the cue
            return True
        return False

    def _extract_dialogue(
        self,
        body_lines: list[str],
        char_indices: list[int],
    ) -> list[tuple[int, list[str], set[int]]]:
        """
        Associate dialogue blocks with preceding character cues.

        Returns list of (char_line_index, [dialogue_text], {source_line_indices}).

        The third element is the exact set of body_lines indices consumed as
        dialogue or parenthetical content, enabling _extract_description to
        exclude them precisely even when blank lines were skipped.

        Dialogue stops when:
          - A blank line is encountered that is NOT followed by a parenthetical.
          - A new character cue or scene heading is encountered.
        Parenthetical lines '(...)' inside a dialogue block are kept.
        """
        if not char_indices:
            return []

        char_index_set = set(char_indices)
        result: list[tuple[int, list[str], set[int]]] = []

        for char_idx in char_indices:
            dlg_lines: list[str] = []
            consumed: set[int] = set()
            i = char_idx + 1
            while i < len(body_lines):
                raw = body_lines[i]
                stripped = raw.strip()

                if not stripped:
                    # Blank line: peek ahead for parenthetical continuation
                    if i + 1 < len(body_lines) and re.match(
                        r"^\s*\(", body_lines[i + 1]
                    ):
                        # Skip the blank; the parenthetical at i+1 is processed
                        # on the next iteration — do NOT advance i here so that
                        # the parenthetical line is picked up normally.
                        i += 1
                        continue
                    break  # End of dialogue block

                if self._is_scene_heading(raw):
                    break
                if i in char_index_set:
                    break
                if self._is_transition(stripped):
                    break

                dlg_lines.append(stripped)
                consumed.add(i)
                i += 1

            if dlg_lines:
                result.append((char_idx, dlg_lines, consumed))

        return result

    def _extract_mood(self, text: str, language: str) -> str:
        """
        Keyword-based mood detection with deterministic tie-breaking.

        Tie-break precedence: dark > tense > romantic > neutral.
        Returns the winning category label.
        """
        lang_key = "ar" if language == "ar" else "en"
        keyword_table = _MOOD_KEYWORDS.get(lang_key, _MOOD_KEYWORDS["en"])

        scores: dict[str, int] = {cat: 0 for cat in keyword_table}
        text_lower = text.lower()

        for category, keywords in keyword_table.items():
            for kw in keywords:
                if lang_key == "en":
                    # Whole-word matching for English
                    scores[category] += len(
                        re.findall(r"\b" + re.escape(kw) + r"\b", text_lower)
                    )
                else:
                    # Substring matching for Arabic
                    scores[category] += text_lower.count(kw)

        # Pick category with highest score; tie-break by precedence
        best = "neutral"
        best_score = 0
        for category in _MOOD_PRECEDENCE:  # ascending precedence
            if category == "neutral":
                continue
            s = scores.get(category, 0)
            if s > best_score or (s == best_score and s > 0):
                best_score = s
                best = category

        return best

    def _extract_description(
        self,
        body_lines: list[str],
        char_index_set: set[int],
        dialogue_line_set: set[int],
    ) -> str:
        """
        Collect action/description lines: not character cues, not dialogue, not blank.
        """
        desc_lines: list[str] = []
        for i, line in enumerate(body_lines):
            if i in char_index_set:
                continue
            if i in dialogue_line_set:
                continue
            stripped = line.strip()
            if stripped:
                desc_lines.append(stripped)
        return "\n".join(desc_lines)

    # ---------------------------------------------------------------------------
    # Title derivation
    # ---------------------------------------------------------------------------

    def _derive_title(self, filename: str) -> str:
        """Derive a human-readable title from the filename stem."""
        stem = Path(filename).stem
        title = stem.replace("_", " ").replace("-", " ").strip()
        return title.title()
