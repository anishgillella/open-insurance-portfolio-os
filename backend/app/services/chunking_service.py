"""Document Chunking Service for Large Document Processing.

This service provides intelligent document chunking with:
- Page-boundary aware splitting
- Configurable overlap for context preservation
- Metadata tracking for chunk provenance
- Table-aware splitting (avoids breaking markdown tables)
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
    chunk_type: str | None = None  # 'text', 'table', 'mixed'

    @property
    def page_range(self) -> str:
        """Human-readable page range."""
        if self.start_page is None:
            return "unknown"
        if self.end_page is None or self.start_page == self.end_page:
            return f"page {self.start_page}"
        return f"pages {self.start_page}-{self.end_page}"

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage."""
        return {
            "index": self.index,
            "content": self.content,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "chunk_type": self.chunk_type,
        }


class ChunkingService:
    """Service for intelligent document chunking.

    Splits documents into overlapping chunks while respecting:
    - Page boundaries (from OCR markers)
    - Paragraph boundaries
    - Section headers
    - Table boundaries (markdown tables)
    """

    # Optimized for RAG: ~1000-1500 tokens = ~4000-6000 chars
    DEFAULT_MAX_CHARS = 4_000
    DEFAULT_OVERLAP_CHARS = 400
    DEFAULT_SINGLE_PASS_THRESHOLD = 5_000

    # Pattern for page markers from OCR
    PAGE_MARKER_PATTERN = re.compile(r"<!-- Page (\d+) -->")

    # Pattern for section headers (ALL CAPS lines or lines ending with :)
    SECTION_HEADER_PATTERN = re.compile(r"^[A-Z][A-Z\s\d]+:?\s*$", re.MULTILINE)

    # Pattern for markdown table rows
    TABLE_ROW_PATTERN = re.compile(r"^\|.*\|$", re.MULTILINE)

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

            # Detect chunk type
            chunk_type = self._detect_chunk_type(chunk_content)

            chunks.append(
                DocumentChunk(
                    index=chunk_index,
                    content=chunk_content,
                    start_page=start_page,
                    end_page=end_page,
                    char_start=current_pos,
                    char_end=chunk_end,
                    chunk_type=chunk_type,
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

    def _detect_chunk_type(self, content: str) -> str:
        """Detect the type of content in a chunk.

        Args:
            content: Chunk content.

        Returns:
            'table' if mostly table content, 'text' if mostly text, 'mixed' if both.
        """
        table_rows = len(self.TABLE_ROW_PATTERN.findall(content))
        total_lines = content.count("\n") + 1

        if table_rows == 0:
            return "text"
        elif table_rows > total_lines * 0.7:
            return "table"
        else:
            return "mixed"

    def _is_inside_table(self, text: str, pos: int) -> bool:
        """Check if position is inside a markdown table.

        Args:
            text: Full document text.
            pos: Character position.

        Returns:
            True if position is within a table.
        """
        # Look for table separator row (| --- | --- |) before and after position
        search_start = max(0, pos - 500)
        search_end = min(len(text), pos + 500)
        context = text[search_start:search_end]

        # Check if there's a table separator in the context
        table_separator = re.search(r"\|\s*[-:]+\s*\|", context)
        if not table_separator:
            return False

        # Check if the position is between table rows
        lines_before = text[search_start:pos].split("\n")
        lines_after = text[pos:search_end].split("\n")

        if lines_before and lines_before[-1].strip().startswith("|"):
            if lines_after and lines_after[0].strip().startswith("|"):
                return True

        return False


# Singleton instances for different use cases
_chunking_service: ChunkingService | None = None
_rag_chunking_service: ChunkingService | None = None


def get_chunking_service() -> ChunkingService:
    """Get or create default chunking service instance.

    This uses the original large chunk settings for LLM extraction.
    """
    global _chunking_service
    if _chunking_service is None:
        # Large chunks for LLM extraction (original settings)
        _chunking_service = ChunkingService(
            max_chars=50_000,
            overlap_chars=2_000,
            single_pass_threshold=60_000,
        )
    return _chunking_service


def get_rag_chunking_service() -> ChunkingService:
    """Get or create RAG-optimized chunking service instance.

    This uses smaller chunks optimized for vector search.
    """
    global _rag_chunking_service
    if _rag_chunking_service is None:
        # Smaller chunks for RAG (new settings)
        _rag_chunking_service = ChunkingService(
            max_chars=4_000,
            overlap_chars=400,
            single_pass_threshold=5_000,
        )
    return _rag_chunking_service
