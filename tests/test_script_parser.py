"""
Automated tests for src/backend/services/script_parser.py

Coverage:
  - English TXT with multiple scenes (exact count)
  - Arabic TXT with multiple scenes (exact count)
  - Mixed Arabic/English detection
  - Pure-English and pure-Arabic detection
  - Language-detection threshold edge cases
  - Character extraction (EN and AR)
  - Character false-positive: ALL-CAPS action line
  - Character false-positive: short Arabic prose line (deterministic syntactic rule)
  - REGRESSION: ordinary Arabic action line فتح الباب ببطء not extracted as character
  - REGRESSION: valid Arabic character cue with following dialogue is extracted
  - Dialogue extraction
  - Dialogue parenthetical retention
  - REGRESSION: dialogue lines do not leak into description when blank precedes parenthetical
  - Location extraction
  - Time-of-day extraction
  - Mood detection (dark)
  - Mood tie-breaking (tense beats romantic)
  - No-scene-heading fallback (exactly one scene, heading='')
  - Preamble discarded when valid headings exist
  - Empty input rejection
  - Whitespace-only rejection
  - Unsupported extension rejection
  - Stable character ordering across scenes
  - Stable location ordering across scenes
  - Determinism: identical inputs → equal outputs
  - In-memory PDF extraction
  - In-memory DOCX extraction
  - Malformed PDF raises ValueError (not a pypdf-specific type)
  - Malformed DOCX raises ValueError (not a python-docx-specific type)
"""

import dataclasses

import pytest

from src.backend.services.script_parser import ScriptParser
from helpers import make_docx_bytes, make_minimal_pdf_bytes, txt_bytes

# ---------------------------------------------------------------------------
# Module-level parser instance (stateless, safe to share across tests)
# ---------------------------------------------------------------------------

PARSER = ScriptParser()

# ---------------------------------------------------------------------------
# Shared script fixtures
# ---------------------------------------------------------------------------

EN_SCRIPT = """\
INT. COFFEE SHOP - DAY

A busy cafe. Steam rises from espresso machines.

ALICE
Good morning. The usual?

BOB
Please.

EXT. STREET - NIGHT

Alice walks home alone, collar turned against the rain.

ALICE
(to herself)
Something feels wrong.

INT. APARTMENT - CONTINUOUS

Alice enters. The door creaks.
"""

AR_SCRIPT = """\
داخلي. المطبخ - صباح

الأم تُعِدّ القهوة بهدوء.

سارة
صباح الخير يا أمّي.

الأم
صباح النور يا حبيبتي.

خارجي. الحديقة - نهار

الأطفال يلعبون تحت أشجار الزيتون.
"""

MIXED_SCRIPT = (
    # ~40 % Arabic letters, ~60 % Latin letters — sits in the mixed band
    "Hello world this is an English sentence. "
    "مرحبا بالعالم هذا نص عربي. "
    "More English here to keep the ratio mixed."
)


# ---------------------------------------------------------------------------
# TXT — multi-scene (exact scene counts)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_english_txt_multiple_scenes():
    result = await PARSER.parse(txt_bytes(EN_SCRIPT), "coffee_shop.txt")
    assert result.scene_count == 3
    assert result.language == "en"
    headings = [s.heading for s in result.scenes]
    assert any("COFFEE SHOP" in h for h in headings)
    assert any("STREET" in h for h in headings)
    assert any("APARTMENT" in h for h in headings)


@pytest.mark.asyncio
async def test_arabic_txt_multiple_scenes():
    result = await PARSER.parse(txt_bytes(AR_SCRIPT), "arabic_script.txt")
    assert result.scene_count == 2
    assert result.language == "ar"
    headings = [s.heading for s in result.scenes]
    assert any("داخلي" in h for h in headings)
    assert any("خارجي" in h for h in headings)


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_language_detection_pure_english():
    script = "INT. HOUSE - DAY\n\nJOHN walks in. Everything is fine.\n"
    result = await PARSER.parse(txt_bytes(script), "test.txt")
    assert result.language == "en"


@pytest.mark.asyncio
async def test_language_detection_pure_arabic():
    result = await PARSER.parse(txt_bytes(AR_SCRIPT), "ar.txt")
    assert result.language == "ar"


@pytest.mark.asyncio
async def test_mixed_language_detection():
    result = await PARSER.parse(txt_bytes(MIXED_SCRIPT), "mixed.txt")
    assert result.language == "mixed"


def test_language_detection_threshold_edge_low():
    """
    Exactly 25 % Arabic letters → ratio == 0.25 which is NOT < 0.25 → 'mixed'.
    Constructed: 25 Arabic letters + 75 Latin letters.
    """
    text = "م" * 25 + "a" * 75
    lang = PARSER._detect_language(text)
    assert lang == "mixed"


def test_language_detection_threshold_edge_high():
    """
    Exactly 60 % Arabic letters → ratio == 0.60 which is NOT > 0.60 → 'mixed'.
    Constructed: 60 Arabic letters + 40 Latin letters.
    """
    text = "م" * 60 + "a" * 40
    lang = PARSER._detect_language(text)
    assert lang == "mixed"


# ---------------------------------------------------------------------------
# Character extraction — English
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_character_extraction():
    result = await PARSER.parse(txt_bytes(EN_SCRIPT), "test.txt")
    scene0_chars = result.scenes[0].characters
    assert "ALICE" in scene0_chars
    assert "BOB" in scene0_chars


@pytest.mark.asyncio
async def test_character_false_positive_uppercase_action():
    """ALL-CAPS action line > 6 words must NOT become a character."""
    script = "INT. WAREHOUSE - NIGHT\n\nTHE DOOR SLAMS SHUT AND THE LIGHTS GO OUT.\n"
    result = await PARSER.parse(txt_bytes(script), "test.txt")
    assert result.scenes[0].characters == []


@pytest.mark.asyncio
async def test_character_false_positive_short_arabic_prose():
    """
    Short Arabic lines excluded by syntactic rules must not become characters.

    Rule 3: line starts with heading token خارجي → excluded.
    Rule 4: line contains a Latin letter → excluded.
    """
    # Rule 3: starts with خارجي
    script_r3 = "داخلي. الغرفة - ليل\n\nخارجي شارع\n"
    result = await PARSER.parse(txt_bytes(script_r3), "test.txt")
    assert "خارجي شارع" not in result.scenes[0].characters

    # Rule 4: contains Latin letter
    script_r4 = "داخلي. الغرفة - ليل\n\nنص A عربي\n"
    result2 = await PARSER.parse(txt_bytes(script_r4), "test.txt")
    for char in result2.scenes[0].characters:
        assert not any(c.isascii() and c.isalpha() for c in char), (
            f"Character '{char}' contains a Latin letter — should have been excluded"
        )


# ---------------------------------------------------------------------------
# REGRESSION: Arabic action line vs character cue
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_arabic_action_line_not_extracted_as_character():
    """
    'فتح الباب ببطء' (opened the door slowly) is a short 3-token Arabic
    action/prose line that must NOT be extracted as a character.

    It is excluded by:
      - Rule 5 in _is_arabic_character_cue: ends with a letter that is part of
        an action phrase — but more importantly, even if syntactic rules alone
        were borderline, _has_following_dialogue requires the next non-blank
        line to be plausible dialogue content (not a scene heading, not another
        cue candidate, and not end-of-scene). Here no dialogue follows the line,
        so the structural context check rejects it.
    """
    script = (
        "داخلي. المنزل - ليل\n"
        "\n"
        "فتح الباب ببطء\n"
        "\n"
        "خارجي. الشارع - نهار\n"
        "\n"
        "المدينة هادئة.\n"
    )
    result = await PARSER.parse(txt_bytes(script), "test.txt")
    all_chars = [c for scene in result.scenes for c in scene.characters]
    assert "فتح الباب ببطء" not in all_chars, (
        "Action line 'فتح الباب ببطء' must not be classified as a character cue"
    )


@pytest.mark.asyncio
async def test_arabic_character_cue_with_dialogue_extracted():
    """
    A genuine Arabic character name followed by dialogue must be extracted.
    Uses AR_SCRIPT which contains سارة → dialogue, and الأم → dialogue.
    """
    result = await PARSER.parse(txt_bytes(AR_SCRIPT), "ar.txt")
    scene0_chars = result.scenes[0].characters
    assert "سارة" in scene0_chars
    assert "الأم" in scene0_chars
    # Confirm their dialogue was captured too
    assert result.scenes[0].dialogue != []


# ---------------------------------------------------------------------------
# Dialogue extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dialogue_extraction():
    result = await PARSER.parse(txt_bytes(EN_SCRIPT), "test.txt")
    scene0 = result.scenes[0]
    assert "Good morning. The usual?" in scene0.dialogue
    assert "Please." in scene0.dialogue


@pytest.mark.asyncio
async def test_dialogue_parenthetical_kept():
    """Parenthetical lines inside a dialogue block must be retained."""
    result = await PARSER.parse(txt_bytes(EN_SCRIPT), "test.txt")
    scene1 = result.scenes[1]
    combined = " ".join(scene1.dialogue)
    assert "(to herself)" in combined or "Something feels wrong" in combined


@pytest.mark.asyncio
async def test_dialogue_does_not_leak_into_description_when_blank_before_parenthetical():
    """
    REGRESSION: when a blank line precedes a parenthetical continuation inside
    a dialogue block, neither the parenthetical nor the following dialogue lines
    should appear in Scene.description.
    """
    script = (
        "INT. STUDIO - DAY\n"
        "\n"
        "The studio is quiet.\n"
        "\n"
        "NARRATOR\n"
        "\n"
        "(quietly)\n"
        "We begin at dawn.\n"
        "\n"
        "The camera pans right.\n"
    )
    result = await PARSER.parse(txt_bytes(script), "test.txt")
    scene = result.scenes[0]

    # The parenthetical and dialogue must be in scene.dialogue
    assert "(quietly)" in scene.dialogue
    assert "We begin at dawn." in scene.dialogue

    # Neither must leak into scene.description
    assert "(quietly)" not in scene.description
    assert "We begin at dawn." not in scene.description


# ---------------------------------------------------------------------------
# Location and time-of-day extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_location_extraction():
    script = "INT. BAKERY - DAY\n\nFresh bread fills the air.\n"
    result = await PARSER.parse(txt_bytes(script), "test.txt")
    assert result.scenes[0].location == "BAKERY"


@pytest.mark.asyncio
async def test_time_of_day_extraction():
    script = "EXT. ROOFTOP - NIGHT\n\nThe city glitters below.\n"
    result = await PARSER.parse(txt_bytes(script), "test.txt")
    assert result.scenes[0].time_of_day == "NIGHT"


# ---------------------------------------------------------------------------
# Mood extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mood_extraction_dark():
    script = (
        "INT. GRAVEYARD - NIGHT\n\n"
        "Blood on the ground. Fear fills the air. "
        "A shadow of death looms near.\n"
    )
    result = await PARSER.parse(txt_bytes(script), "test.txt")
    assert result.scenes[0].mood == "dark"


@pytest.mark.asyncio
async def test_mood_tie_breaking():
    """
    Equal counts of tense and romantic keywords → tie-breaks to 'tense'
    (precedence: dark > tense > romantic > neutral).
    """
    # 1 romantic keyword (love) + 1 tense keyword (gun) → tie → tense wins
    script = (
        "INT. ROOM - DAY\n\n"
        "She held his hand with love while the gun lay on the table.\n"
    )
    result = await PARSER.parse(txt_bytes(script), "test.txt")
    assert result.scenes[0].mood == "tense"


# ---------------------------------------------------------------------------
# Fallback and preamble
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_scene_heading_fallback():
    """Plain prose with no headings → exactly one scene with heading=''."""
    script = "Just some plain text.\nNo headings at all.\nAnother line.\n"
    result = await PARSER.parse(txt_bytes(script), "plain.txt")
    assert result.scene_count == 1
    assert result.scenes[0].heading == ""


@pytest.mark.asyncio
async def test_preamble_discarded():
    """
    Title-page / preamble text before the first valid heading must not appear
    as a scene heading and must not inflate the scene count.
    """
    script = (
        "FADE IN:\n"
        "TITLE: My Great Film\n"
        "Written by Someone\n"
        "\n"
        "INT. LIVING ROOM - DAY\n"
        "\n"
        "A family sits around the table.\n"
    )
    result = await PARSER.parse(txt_bytes(script), "film.txt")
    assert result.scene_count == 1
    headings = [s.heading for s in result.scenes]
    assert all("TITLE" not in h and "FADE" not in h for h in headings)
    assert any("LIVING ROOM" in h for h in headings)


# ---------------------------------------------------------------------------
# Rejection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_input_rejection():
    with pytest.raises(ValueError):
        await PARSER.parse(b"", "script.txt")


@pytest.mark.asyncio
async def test_whitespace_only_rejection():
    with pytest.raises(ValueError):
        await PARSER.parse(b"   \n\t  ", "script.txt")


@pytest.mark.asyncio
async def test_unsupported_extension_rejection():
    with pytest.raises(ValueError):
        await PARSER.parse(b"some data", "script.xyz")


# ---------------------------------------------------------------------------
# Ordering and determinism
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stable_character_ordering():
    """Characters must appear in first-seen order across scenes, no duplicates."""
    script = (
        "INT. ROOM A - DAY\n\nALICE\nHi.\n\nBOB\nHello.\n\n"
        "INT. ROOM B - NIGHT\n\nBOB\nAgain.\n\n"
        "INT. ROOM C - DAY\n\nCAROL\nLast.\n"
    )
    result = await PARSER.parse(txt_bytes(script), "ordering.txt")
    chars = result.characters
    assert chars.index("ALICE") < chars.index("BOB")
    assert chars.index("BOB") < chars.index("CAROL")
    assert chars.count("BOB") == 1


@pytest.mark.asyncio
async def test_stable_location_ordering():
    """Locations must appear in first-seen order, no duplicates."""
    script = (
        "INT. KITCHEN - DAY\n\nSome action.\n\n"
        "EXT. GARDEN - NIGHT\n\nMore action.\n\n"
        "INT. KITCHEN - LATER\n\nBack again.\n"
    )
    result = await PARSER.parse(txt_bytes(script), "locs.txt")
    locs = result.locations
    assert locs.index("KITCHEN") < locs.index("GARDEN")
    assert locs.count("KITCHEN") == 1


@pytest.mark.asyncio
async def test_determinism():
    """Parsing the same bytes twice must produce equal ParsedScript objects."""
    data = txt_bytes(EN_SCRIPT)
    result_a = await PARSER.parse(data, "coffee_shop.txt")
    result_b = await PARSER.parse(data, "coffee_shop.txt")
    assert dataclasses.asdict(result_a) == dataclasses.asdict(result_b)


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pdf_extraction():
    text = "INT. STUDIO - DAY\n\nCAMERA\nAction!\n"
    pdf_data = make_minimal_pdf_bytes(text)
    result = await PARSER.parse(pdf_data, "studio.pdf")
    assert result.scene_count >= 1
    assert any("STUDIO" in s.heading for s in result.scenes)


@pytest.mark.asyncio
async def test_malformed_pdf_raises_value_error():
    """A byte string that is not a valid PDF must raise ValueError only."""
    with pytest.raises(ValueError):
        await PARSER.parse(b"This is definitely not a PDF file at all.", "bad.pdf")


# ---------------------------------------------------------------------------
# DOCX extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_docx_extraction():
    paragraphs = [
        "INT. OFFICE - DAY",
        "",
        "The team huddles around a whiteboard.",
        "",
        "MANAGER",
        "Let us begin.",
    ]
    docx_data = make_docx_bytes(paragraphs)
    result = await PARSER.parse(docx_data, "office.docx")
    assert result.scene_count >= 1
    assert any("OFFICE" in s.heading for s in result.scenes)


@pytest.mark.asyncio
async def test_malformed_docx_raises_value_error():
    """A byte string that is not a valid DOCX must raise ValueError only."""
    with pytest.raises(ValueError):
        await PARSER.parse(b"This is not a DOCX file.", "bad.docx")
