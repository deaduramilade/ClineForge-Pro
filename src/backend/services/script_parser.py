"""
Script parser service.

Owned by: Data Science Lead
Responsibility: Parse Arabic and English script files into structured scene breakdowns.

TODO:
- Implement PDF/DOCX/TXT parsing
- Implement bilingual scene segmentation (Arabic + English)
- Extract characters, locations, mood, and dialogue per scene
"""

from dataclasses import dataclass, field


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


class ScriptParser:
    """
    Parse film scripts (Arabic and English) into structured scene data.

    Usage:
        parser = ScriptParser()
        result = await parser.parse(file_bytes, filename="script.pdf")
    """

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedScript:
        """
        Parse a script file and return structured scene data.

        Args:
            file_bytes: Raw (decrypted) file content
            filename: Original filename (used to detect format)

        Returns:
            ParsedScript with scene breakdown
        """
        raise NotImplementedError(
            "ScriptParser.parse() is not yet implemented. "
            "See Data Science Lead responsibilities in CHARTER.md."
        )

    def _detect_language(self, text: str) -> str:
        """Detect whether the script is primarily Arabic or English."""
        arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
        return "ar" if arabic_chars / max(len(text), 1) > 0.3 else "en"
