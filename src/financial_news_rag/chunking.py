from __future__ import annotations

import hashlib
import re

from .models import Chunk, ParsedDocument


TOKEN_PATTERN = re.compile(r"[\u3400-\u9fff]|[A-Za-z0-9_]+|[^\s]", re.UNICODE)


class TokenChunker:
    """Token-like chunking that preserves the original Chinese text spans."""

    def __init__(self, chunk_size: int = 1024, overlap: int = 256):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, document: ParsedDocument) -> list[Chunk]:
        chunks: list[Chunk] = []
        chunk_index = 0
        for page in document.pages:
            text = page.text.strip()
            if not text:
                continue
            matches = list(TOKEN_PATTERN.finditer(text))
            if not matches:
                continue
            start = 0
            while start < len(matches):
                stop = min(start + self.chunk_size, len(matches))
                char_start = matches[start].start()
                char_stop = matches[stop - 1].end()
                content = text[char_start:char_stop].strip()
                if content:
                    digest = hashlib.sha256(
                        f"{document.doc_id}:{page.page_number}:{chunk_index}:{content}".encode(
                            "utf-8"
                        )
                    ).hexdigest()[:24]
                    chunks.append(
                        Chunk(
                            chunk_id=digest,
                            doc_id=document.doc_id,
                            content=content,
                            title=document.title,
                            source=document.source,
                            page_number=page.page_number,
                            publish_time=document.publish_time,
                            chunk_index=chunk_index,
                            metadata=dict(document.metadata),
                        )
                    )
                    chunk_index += 1
                if stop == len(matches):
                    break
                start = stop - self.overlap
        return chunks
