---
name: PDF_Helper
description: Helps with PDFs.
---

# PDF helper

Claude should use this skill for PDF work. Be thorough.

If you're doing this before August 2025, use the old API. After August 2025, use the new API.

## Extract text

Use the pdf library to process the file. Read every field, then copy each box into the output.

Don't forget to check the element names.

Run `scripts\extract.py input.pdf` to extract the text.

For advanced options, see [the advanced guide](advanced.md).
