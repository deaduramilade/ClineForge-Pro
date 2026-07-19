"""
Reusable in-memory fixture builders for the script parser test suite.

Import these helpers directly in test modules:
    from helpers import txt_bytes, make_docx_bytes, make_minimal_pdf_bytes
"""

import io


def txt_bytes(s: str) -> bytes:
    """Encode a string as UTF-8 bytes for use as a .txt script fixture."""
    return s.encode("utf-8")


def make_docx_bytes(paragraphs: list) -> bytes:
    """
    Build a real in-memory DOCX using python-docx.
    Returns the raw bytes that ScriptParser._extract_docx expects.
    """
    import docx  # python-docx

    buf = io.BytesIO()
    doc = docx.Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    doc.save(buf)
    return buf.getvalue()


def make_minimal_pdf_bytes(text: str) -> bytes:
    """
    Build a minimal but structurally valid PDF containing the given text.

    The PDF is constructed entirely from Python string/bytes operations —
    no third-party library required. Byte offsets in the cross-reference
    table are calculated dynamically from the actual object lengths, so
    the file is valid for pypdf to parse.

    Structure:
        %PDF-1.4
        1 0 obj  — catalog
        2 0 obj  — pages node
        3 0 obj  — page
        4 0 obj  — content stream
        5 0 obj  — font resource
        xref + trailer
    """
    # Escape special PDF string characters
    escaped = (
        text.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .replace("\r", "\\r")
    )

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"

    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = (
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] "
        b"/Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>\n"
        b"endobj\n"
    )

    stream_data = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET\n".encode("latin-1")
    stream_len = len(stream_data)
    obj4 = (
        f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("latin-1")
        + stream_data
        + b"\nendstream\nendobj\n"
    )
    obj5 = (
        b"5 0 obj\n"
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"
        b"endobj\n"
    )

    # Calculate byte offsets dynamically from actual object lengths
    chunks = [obj1, obj2, obj3, obj4, obj5]
    offsets: list[int] = []
    pos = len(header)
    for chunk in chunks:
        offsets.append(pos)
        pos += len(chunk)

    xref_offset = pos

    xref = b"xref\n"
    xref += b"0 6\n"
    xref += b"0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode("ascii")

    trailer = (
        f"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")

    return header + b"".join(chunks) + xref + trailer
