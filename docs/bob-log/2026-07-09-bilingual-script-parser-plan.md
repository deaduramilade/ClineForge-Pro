# Bilingual Script Parser — Implementation Plan (Revised)

## Top-Level Overview

**Goal:** Implement a deterministic, fully-testable bilingual (Arabic/English) script-parsing
pipeline inside `src/backend/services/script_parser.py` and cover it with automated tests in a
new `tests/` directory.

**Scope (exact file boundaries):**

| Action | File |
|--------|------|
| Modify | `src/backend/services/script_parser.py` |
| Create | `tests/__init__.py` |
| Create | `tests/conftest.py` |
| Create | `tests/test_script_parser.py` |

No other files are touched. Requirements.txt, routers, schemas, main.py, and all frontend files
are out of scope.

**Existing public surface — must be preserved byte-for-byte:**

```python
@dataclass
class Scene:
    index: int
    heading: str
    description: str
    characters: list[str] = field(default_factory=list)
    location: str = ""
    time_of_day: str = ""
    mood: str = ""
    dialogue: list[str] = field(default_factory=list)
    language: str = "en"   # 'en' or 'ar'

@dataclass
class ParsedScript:
    title: str
    language: str
    scene_count: int
    scenes: list[Scene] = field(default_factory=list)
    characters: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)

class ScriptParser:
    async def parse(self, file_bytes: bytes, filename: str) -> ParsedScript: ...
```

**No external AI calls anywhere in the parser. All logic is deterministic.**

**All declared dependencies are already in `requirements.txt`:** `pypdf==4.3.1`,
`python-docx==1.1.2`, `pytest==8.3.2`, `pytest-asyncio==0.23.8`.

---

## Sub-Task 1 — Implement the Core Script Parser

### Intent
Replace the `NotImplementedError` stub in `ScriptParser.parse()` with a complete, modular
implementation. All behaviour is captured in private helper methods. `Scene` and `ParsedScript`
dataclasses and `parse()` signature are unchanged.

### Expected Outcomes
- `parse()` extracts text from `.txt`, `.pdf`, `.docx` inputs.
- `.pdf` and `.docx` inputs are processed in-memory via `BytesIO`; no temp files written.
- Unsupported extensions raise `ValueError` with a clear, user-readable message.
- Empty files and files that produce no extractable text raise `ValueError`.
- Language detection operates only on meaningful letter characters (Arabic-script and Latin
  letters), ignoring digits, punctuation, whitespace, and combining marks.
- Scripts are segmented into scenes with heading-based heuristics; preamble text before the
  first valid heading is discarded, not promoted to a phantom scene.
- When no valid heading exists, exactly one fallback `Scene` is produced containing the full
  content.
- Every `Scene` field is populated as reliably as possible.
- `ParsedScript.characters` and `.locations` are in first-seen order, deduplicated
  case-insensitively; the stored value is the first-seen casing.
- `parse()` is deterministic: identical `(file_bytes, filename)` inputs always produce equal
  `ParsedScript` outputs.
- No IBM Granite / watsonx.ai calls anywhere.

### Todo List

#### 1a. Text extraction
1. Add `_extract_text(file_bytes: bytes, ext: str) -> str` — dispatch by extension; raise
   `ValueError("Unsupported file type: .<ext>")` for anything other than `.txt`, `.pdf`,
   `.docx`.
2. Add `_extract_txt(file_bytes: bytes) -> str` — try `utf-8-sig` first (handles BOM), then
   `utf-8`; if both fail, raise `ValueError("TXT file is not valid UTF-8")`. Do **not** fall
   back to latin-1.
3. Add `_extract_pdf(file_bytes: bytes) -> str` — use `pypdf.PdfReader(BytesIO(data))` →
   concatenate `page.extract_text() or ""` for all pages. If the joined result is blank after
   stripping, raise `ValueError("PDF contains no extractable text (possibly scanned)")`.
   Wrap `pypdf` exceptions in `ValueError` so callers never see a `pypdf`-specific type.
4. Add `_extract_docx(file_bytes: bytes) -> str` — use `docx.Document(BytesIO(data))` →
   join `p.text` for all paragraphs. If result is blank, raise
   `ValueError("DOCX contains no extractable text")`. Wrap `python-docx` exceptions in
   `ValueError`.
5. Add `_validate_text(text: str)` — raise `ValueError("Script is empty or contains no
   meaningful text")` when `text.strip()` is empty.

#### 1b. Language detection
6. Revise `_detect_language(text: str) -> str` — count only letters in the Unicode categories
   `Lo`, `Ll`, `Lu`, `Lt`, `Lm` using `unicodedata.category(c)`. Within those, a character is
   *Arabic-script* if it falls in any of: Arabic (U+0600–U+06FF), Arabic Supplement
   (U+0750–U+077F), Arabic Extended-A (U+08A0–U+08FF), Arabic Presentation Forms-A
   (U+FB50–U+FDFF), Arabic Presentation Forms-B (U+FE70–U+FEFF). Everything else counts as
   *other-script*. Thresholds: Arabic fraction > 0.60 → `"ar"`, < 0.25 → `"en"`,
   between 0.25–0.60 inclusive → `"mixed"`. If no letter characters are found, return `"en"`.

#### 1c. Scene segmentation
7. Add `_build_heading_regex() -> re.Pattern` — compile once (store on the class). Matches
   lines that start (after optional leading whitespace) with one of:
   - English tokens: `INT.`, `EXT.`, `INT/EXT.`, `I/E.`, `INT./EXT.`, case-insensitive.
   - Arabic tokens: `داخلي`, `خارجي` (with or without trailing `.` or `:`).
   The rest of the line (location, separator, time) is captured but not required — the key
   constraint is that the *prefix* must match one of the tokens above. This avoids false
   positives from ordinary prose.
8. Add `_split_into_scenes(lines: list[str]) -> list[tuple[str, list[str]]]` — returns a list
   of `(heading, body_lines)` pairs. Lines before the first matching heading are collected as
   preamble and silently discarded. If no heading is found, return
   `[("", lines)]` (one fallback scene). Heading text is preserved exactly as found in the
   source (no normalisation of casing here).

#### 1d. Per-scene field extraction
9. Add `_extract_location_time(heading: str) -> tuple[str, str]` — returns
   `(location, time_of_day)`. For English: split on first `.` to remove prefix token, then
   split on ` - ` (or ` – `); location is the left part, time_of_day the right (both stripped
   and uppercased). For Arabic headings starting with داخلي/خارجي: apply the same dash-split
   pattern. Return `("", "")` if no structure is found.
10. Add `_is_transition(line: str) -> bool` — returns True for known transition lines such as
    `CUT TO:`, `DISSOLVE TO:`, `FADE IN:`, `FADE OUT:`, `SMASH CUT:`, `MATCH CUT:` (matched
    case-insensitively, stripped). These lines must never become characters.
11. Add `_is_scene_heading(line: str) -> bool` — delegates to `_build_heading_regex()`. Used
    as a guard inside character and dialogue extraction.
12. Add `_extract_characters(body_lines: list[str]) -> list[int]` — returns indices of
    character-cue lines. A line qualifies when **all** of these hold:
    - Not blank.
    - Not a scene heading (`_is_scene_heading`).
    - Not a transition (`_is_transition`).
    - For English: the stripped line is ALL-CAPS, contains only ASCII letters, spaces, and
      hyphens, and is ≤ 6 words. Parentheticals `(V.O.)`, `(O.S.)`, `(O.C.)`,
      `(CONT'D)` on the same line are stripped before the word-count check.
    - For Arabic: a short (≤ 5 whitespace-separated tokens) line containing only
      Arabic-script characters and spaces — not starting with a heading token.
    Both cases also require the line to not be a known all-caps action keyword list (e.g.
    `SUPER:`, `TITLE:`, `SMASH CUT`, `THE END`).
13. Add `_extract_dialogue(body_lines: list[str], char_indices: list[int])
    -> list[tuple[int, list[str]]]` — returns `(char_line_idx, [dialogue_lines])` pairs.
    Dialogue is the block of consecutive non-blank lines immediately following a character cue,
    stopping when: a blank line appears that is **not** followed by a parenthetical
    `(...)` continuation, or when a new character cue / scene heading is encountered.
    Parenthetical lines `(...)` inside a dialogue block are kept as part of the dialogue list.
14. Add `_extract_mood(text: str, language: str) -> str` — keyword lookup with four categories
    and tie-breaking:
    - Categories: `"tense"`, `"romantic"`, `"dark"`, `"neutral"`.
    - `"neutral"` is the default/fallback (score 0 for all others).
    - English keywords (sample): tense → `["chase", "gun", "danger", "threat", "alarm",
      "fight", "run", "escape"]`; romantic → `["love", "kiss", "heart", "embrace",
      "together", "darling"]`; dark → `["death", "dead", "blood", "fear", "shadow",
      "kill", "murder", "grave"]`.
    - Arabic equivalents mapped to the same categories.
    - Matching is case-insensitive whole-word for English, substring for Arabic.
    - Tie-breaking (equal counts): category precedence is `dark > tense > romantic > neutral`.
    - Returns the winning category label string.
15. Add `_extract_description(body_lines: list[str], char_indices: list[int],
    dialogue_line_sets: set[int]) -> str` — lines that are neither character cues, dialogue,
    nor blank become the description (joined with `\n`).
16. Add `_parse_scene(index: int, heading: str, body_lines: list[str],
    script_language: str) -> Scene` — calls helpers 9–15, constructs and returns a `Scene`.
    `Scene.language` is set per-scene by running `_detect_language` on the scene's own body
    text (so mixed scripts can have per-scene language tags).

#### 1e. Title derivation and aggregation
17. Add `_derive_title(filename: str) -> str` — `Path(filename).stem`, replace `_` and `-`
    with spaces, strip, title-case.
18. In `parse()`: extract text → validate → detect language → split scenes → parse each scene
    → aggregate unique characters and locations in first-seen order using a case-insensitive
    seen-set (store the first-seen original casing). Set `ParsedScript.scene_count =
    len(scenes)`.

### Relevant Context
- [`src/backend/services/script_parser.py`](src/backend/services/script_parser.py) — exact
  current content inspected; stubs preserved, `_detect_language` replaced.
- `pypdf` API: `pypdf.PdfReader(BytesIO(b))` → `.pages[i].extract_text()`.
- `python-docx` API: `docx.Document(BytesIO(b))` → `.paragraphs[i].text`.
- Standard library only: `re`, `unicodedata`, `pathlib`, `io.BytesIO`.

### Status
[ ] pending

---

## Sub-Task 2 — Create the Test Suite

### Intent
Create a conventional `tests/` package at the repo root with focused unit tests that verify
every required scenario. All test inputs are constructed in-memory (strings → bytes for TXT;
`fpdf2`-free raw minimal PDF bytes; `python-docx` `Document()` API for DOCX). No binary fixture
files are added to the repository.

### Expected Outcomes
- `tests/__init__.py` (empty file).
- `tests/conftest.py` with shared helpers/fixtures.
- `tests/test_script_parser.py` with ≥ 23 test cases, all passing.
- `pytest` runs from the repo root and all tests are green.
- No new pip packages are required.

### Todo List

#### 2a. Test infrastructure
1. Create `tests/__init__.py` (empty).
2. Create `tests/conftest.py`:
   - Insert `src/backend` onto `sys.path` so `from services.script_parser import …` resolves.
   - Define `txt_bytes(s: str) -> bytes` helper (encodes as UTF-8).
   - Define `make_docx_bytes(paragraphs: list[str]) -> bytes` helper — builds a real
     `python-docx` `Document` in-memory and calls `doc.save(buf)`.
   - Define `make_minimal_pdf_bytes(text: str) -> bytes` helper — constructs a minimal valid
     PDF entirely from Python string operations (no extra library needed; a bare-bones
     hand-rolled PDF stream is ≈ 20 lines and sufficient for `pypdf` to parse).
3. Annotate all async tests with `@pytest.mark.asyncio`.

#### 2b. TXT tests
4. `test_english_txt_multiple_scenes` — multi-scene EN script (≥ 3 INT./EXT. headings), assert
   `scene_count >= 3`, correct heading strings, `language == "en"`.
5. `test_arabic_txt_multiple_scenes` — multi-scene AR script with `داخلي`/`خارجي` headings,
   assert `scene_count >= 2`, `language == "ar"`.
6. `test_mixed_language_detection` — body text ≈ 40 % Arabic letters, 60 % Latin letters,
   assert `language == "mixed"`.
7. `test_language_detection_pure_english` — all-Latin body, assert `language == "en"`.
8. `test_language_detection_pure_arabic` — all-Arabic body, assert `language == "ar"`.
9. `test_language_detection_threshold_edge` — craft text exactly at the 0.25 / 0.60 boundary
   values and assert the correct bucket is returned.

#### 2c. Field extraction tests
10. `test_character_extraction` — EN script with ≥ 2 character cues; assert `Scene.characters`
    matches expected list.
11. `test_character_false_positive_uppercase_action` — action line in all-caps (e.g.
    `"THE DOOR SLAMS SHUT."`) does **not** appear in `Scene.characters`.
12. `test_character_false_positive_short_arabic_prose` — a short Arabic sentence that is NOT a
    character name does not appear in `Scene.characters`.
13. `test_dialogue_extraction` — character cue followed by dialogue lines; assert
    `Scene.dialogue` contains the expected lines.
14. `test_dialogue_parenthetical_kept` — parenthetical `(O.S.)` inside dialogue block is
    retained in `Scene.dialogue`.
15. `test_location_extraction` — heading `"INT. BAKERY - DAY"`, assert
    `Scene.location == "BAKERY"`.
16. `test_time_of_day_extraction` — heading `"EXT. ROOFTOP - NIGHT"`, assert
    `Scene.time_of_day == "NIGHT"`.
17. `test_mood_extraction_dark` — body text contains dark keywords, assert `mood == "dark"`.
18. `test_mood_tie_breaking` — body text contains equal counts of tense and romantic keywords;
    assert tie resolves to `"tense"` (dark > tense > romantic precedence).
19. `test_no_scene_heading_fallback` — plain prose with no headings; assert `scene_count == 1`
    and the single scene has `heading == ""`.
20. `test_preamble_discarded` — title-page text followed by a valid INT. heading; assert the
    preamble text is not in any scene heading.

#### 2d. Rejection tests
21. `test_empty_input_rejection` — `parse(b"", "script.txt")` raises `ValueError`.
22. `test_whitespace_only_rejection` — `parse(b"   \n\t  ", "script.txt")` raises `ValueError`.
23. `test_unsupported_extension_rejection` — `parse(b"data", "script.xyz")` raises `ValueError`.

#### 2e. Ordering and determinism tests
24. `test_stable_character_ordering` — two scenes each introducing different characters; assert
    `ParsedScript.characters` is in first-seen order with no duplicates.
25. `test_stable_location_ordering` — same as above for locations.
26. `test_determinism` — call `parse()` twice with the same bytes and filename; assert the two
    `ParsedScript` results are equal (use `dataclasses.asdict` for deep equality).

#### 2f. PDF and DOCX extraction tests
27. `test_pdf_extraction` — build a minimal in-memory PDF with `make_minimal_pdf_bytes`, assert
    parsed scenes and characters match expectations.
28. `test_docx_extraction` — build an in-memory DOCX with `make_docx_bytes`, assert parsed
    scenes match expectations.
29. `test_malformed_pdf_raises_value_error` — pass a byte string that is not a valid PDF with
    extension `.pdf`; assert `ValueError` is raised (not `pypdf.errors.PdfReadError` or any
    other dependency-specific type leaking through).
30. `test_malformed_docx_raises_value_error` — same for `.docx`; assert `ValueError` only.

### Relevant Context
- No existing test infrastructure — create the smallest conventional layout.
- `pytest-asyncio` is in `requirements.txt`; use `@pytest.mark.asyncio` (explicit mode, no
  extra config required).
- Import path: `conftest.py` inserts `src/backend` into `sys.path` so all backend modules
  resolve without installing the package.
- Hand-rolled minimal PDF structure sufficient for `pypdf`: `%PDF-1.4` header + one page
  object tree with a content stream containing a `BT ... ET` text block.
- `python-docx` `Document()` + `doc.add_paragraph(text)` + `BytesIO` save is sufficient for
  DOCX fixture construction without writing to disk.

### Status
[ ] pending

---

## Validation Sequence (after implementation, before reporting)

Performed in this exact order — no step is skipped:

1. **Python compile check** — `python -m py_compile src/backend/services/script_parser.py`
   must exit 0.
2. **Import check** — `python -c "from src.backend.services.script_parser import ScriptParser"`
   (or equivalent with `sys.path` insert) must exit 0.
3. **pytest** — `pytest tests/ -v` from repo root; all tests must pass; output captured and
   reported verbatim.
4. **git diff --check** — must exit 0 (no whitespace errors).
5. **git status --short** — output reported; must show only the four approved files.
6. **git diff review** — full diff inspected to confirm no unapproved files were modified.

Only after all six checks pass is the task reported as complete.

---

## Constraints (hard rules, not relaxed under any circumstance)

- `Scene`, `ParsedScript` dataclass fields, types, defaults, and `parse()` signature are
  preserved exactly as in the current file.
- No latin-1 fallback in TXT decoding.
- No external AI/LLM calls.
- No new packages added; no `requirements.txt` changes.
- No modifications to routers, schemas, `main.py`, or frontend.
- No commits, pushes, merges, branch changes, or package installs.
- Secrets and environment variable values are never printed or exposed.
- Tests are only reported as passed after actual successful execution.

---

## Open Assumptions

| # | Assumption |
|---|-----------|
| A1 | `utf-8-sig` is tried first for TXT to handle BOM transparently; plain `utf-8` is the only fallback. Files that are neither are rejected. |
| A2 | Arabic Unicode ranges covered: U+0600–U+06FF, U+0750–U+077F, U+08A0–U+08FF, U+FB50–U+FDFF, U+FE70–U+FEFF. |
| A3 | Language thresholds: Arabic fraction of meaningful letters > 0.60 → `"ar"`, < 0.25 → `"en"`, else `"mixed"`. |
| A4 | Heading regex anchors to line start (after optional whitespace). Requires the INT./EXT. token; the remainder is optional. |
| A5 | Character cues: EN = ALL-CAPS ≤ 6 words, ASCII letters/spaces/hyphens only (after stripping parentheticals). AR = ≤ 5 tokens, all Arabic-script. Both exclude headings, transitions, and known all-caps action keywords. |
| A6 | Mood tie-break precedence: `dark > tense > romantic > neutral`. |
| A7 | Preamble (text before first valid heading) is silently discarded. |
| A8 | Case normalisation for dedup: `lower()`. First-seen casing is stored. |
| A9 | `ParsedScript.scene_count` equals `len(scenes)` (number of `Scene` objects in the list). |
| A10 | Per-scene `Scene.language` is set by running `_detect_language` on that scene's own body text. |
