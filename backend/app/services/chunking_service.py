"""Document Chunking Service for Large Document Processing.

This service provides intelligent document chunking with:
- Page-boundary aware splitting
- Configurable overlap for context preservation
- Metadata tracking for chunk provenance
"""

import re
from dataclasses import dataclass
from typing import List


@dataclass
class DocumentChunk:
    """A chunk of document text with metadata."""

    index: int
    content: str
    start_page: int | None
    end_page: int | None
    char_start: int
    char_end: int

    @property
    def page_range(self) -> str:
        """Human-readable page range."""
        if self.start_page is None:
            return "unknown"
        if self.end_page is None or self.start_page == self.end_page:
            return f"page {self.start_page}"
        return f"pages {self.start_page}-{self.end_page}"


class ChunkingService:
    """Service for intelligent document chunking.

    Splits documents into overlapping chunks while respecting:
    - Page boundaries (from OCR markers)
    - Paragraph boundaries
    - Section headers
    """

    DEFAULT_MAX_CHARS = 50_000
    DEFAULT_OVERLAP_CHARS = 2_000
    DEFAULT_SINGLE_PASS_THRESHOLD = 60_000

    # Pattern for page markers from OCR
    PAGE_MARKER_PATTERN = re.compile(r"<!-- Page (\d+) -->")

    # Pattern for section headers (ALL CAPS lines or lines ending with :)
    SECTION_HEADER_PATTERN = re.compile(r"^[A-Z][A-Z\s\d]+:?\s*$", re.MULTILINE)

    def __init__(
        self,
        max_chars: int = DEFAULT_MAX_CHARS,
        overlap_chars: int = DEFAULT_OVERLAP_CHARS,
        single_pass_threshold: int = DEFAULT_SINGLE_PASS_THRESHOLD,
    ):
        """Initialize chunking service.

        Args:
            max_chars: Maximum characters per chunk.
            overlap_chars: Overlap between chunks for context preservation.
            single_pass_threshold: Documents smaller than this use single chunk.
        """
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars
        self.single_pass_threshold = single_pass_threshold

    def chunk_document(self, text: str) -> List[DocumentChunk]:
        """Split document into overlapping chunks.

        Strategy:
        1. If document is small enough, return single chunk
        2. Prefer splitting on page boundaries
        3. Fall back to paragraph/section boundaries
        4. Ensure overlap to preserve context

        Args:
            text: Full document text (typically OCR output).

        Returns:
            List of DocumentChunk objects.
        """
        if len(text) <= self.single_pass_threshold:
            return [
                DocumentChunk(
                    index=0,
                    content=text,
                    start_page=1,
                    end_page=self._count_pages(text),
                    char_start=0,
                    char_end=len(text),
                )
            ]

        chunks = []
        current_pos = 0
        chunk_index = 0

        while current_pos < len(text):
            # Calculate chunk end position
            chunk_end = min(current_pos + self.max_chars, len(text))

            # Find best split point (prefer page boundary)
            if chunk_end < len(text):
                split_point = self._find_split_point(
                    text,
                    max(current_pos, chunk_end - self.overlap_chars),
                    min(len(text), chunk_end + self.overlap_chars),
                )
                chunk_end = split_point

            # Extract chunk content
            chunk_content = text[current_pos:chunk_end]

            # Determine page range
            start_page = self._get_page_at_position(text, current_pos)
            end_page = self._get_page_at_position(text, chunk_end)

            chunks.append(
                DocumentChunk(
                    index=chunk_index,
                    content=chunk_content,
                    start_page=start_page,
                    end_page=end_page,
                    char_start=current_pos,
                    char_end=chunk_end,
                )
            )

            # Move position with overlap (but ensure we make progress)
            next_pos = chunk_end - self.overlap_chars
            if next_pos <= current_pos:
                next_pos = chunk_end  # Ensure we always move forward

            current_pos = next_pos
            chunk_index += 1

            # Safety check to prevent infinite loops
            if chunk_index > 100:
                break

        return chunks

    def _find_split_point(self, text: str, min_pos: int, max_pos: int) -> int:
        """Find optimal split point within range.

        Priority:
        1. Page boundary (<!-- Page N -->)
        2. Double newline (paragraph break)
        3. Section header
        4. Single newline
        5. Space

        Args:
            text: Full document text.
            min_pos: Minimum position for split.
            max_pos: Maximum position for split.

        Returns:
            Best split position.
        """
        # Ensure we have valid bounds
        min_pos = max(0, min_pos)
        max_pos = min(len(text), max_pos)

        if min_pos >= max_pos:
            return max_pos

        search_area = text[min_pos:max_pos]

        # Priority 1: Page boundary
        page_matches = list(self.PAGE_MARKER_PATTERN.finditer(search_area))
        if page_matches:
            # Take the last page boundary in the range
            return min_pos + page_matches[-1].start()

        # Priority 2: Double newline (paragraph break)
        para_breaks = [m.start() for m in re.finditer(r"\n\n", search_area)]
        if para_breaks:
            return min_pos + para_breaks[-1]

        # Priority 3: Section header
        header_matches = list(self.SECTION_HEADER_PATTERN.finditer(search_area))
        if header_matches:
            return min_pos + header_matches[-1].start()

        # Priority 4: Single newline
        newlines = [m.start() for m in re.finditer(r"\n", search_area)]
        if newlines:
            return min_pos + newlines[-1]

        # Priority 5: Space
        spaces = [m.start() for m in re.finditer(r" ", search_area)]
        if spaces:
            return min_pos + spaces[-1]

        # Fallback: Just use max_pos
        return max_pos

    def _count_pages(self, text: str) -> int:
        """Count total pages in document.

        Args:
            text: Document text with page markers.

        Returns:
            Number of pages (1 if no markers found).
        """
        matches = self.PAGE_MARKER_PATTERN.findall(text)
        return max([int(m) for m in matches]) if matches else 1

    def _get_page_at_position(self, text: str, pos: int) -> int | None:
        """Get page number at character position.

        Args:
            text: Document text with page markers.
            pos: Character position.

        Returns:
            Page number at position, or 1 if no markers found.
        """
        text_before = text[:pos]
        matches = list(self.PAGE_MARKER_PATTERN.finditer(text_before))
        if matches:
            return int(matches[-1].group(1))
        return 1

    def get_chunk_context(self, chunks: List[DocumentChunk], chunk_index: int) -> str:
        """Get context string for a chunk (useful for prompts).

        Args:
            chunks: List of all chunks.
            chunk_index: Index of the current chunk.

        Returns:
            Context string like "Chunk 2 of 5 (pages 4-7)".
        """
        if chunk_index >= len(chunks):
            return ""

        chunk = chunks[chunk_index]
        return f"Chunk {chunk_index + 1} of {len(chunks)} ({chunk.page_range})"


# Singleton instance
_chunking_service: ChunkingService | None = None


def get_chunking_service() -> ChunkingService:
    """Get or create chunking service instance."""
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
