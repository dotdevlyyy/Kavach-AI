import re
from typing import List


def split_into_sentences(text: str) -> List[str]:
    """Splits text into sentences, preserving punctuation."""
    # Matches a period, exclamation, or question mark, followed by a space or newline.
    sentence_endings = re.compile(r"(?<=[.!?])\s+")
    sentences = sentence_endings.split(text.strip())
    # Filter out empty strings
    return [s.strip() for s in sentences if s.strip()]


def get_word_count(text: str) -> int:
    """Returns the approximate word count of a text."""
    return len(text.split())


def chunk_text(text: str, chunk_size: int = 512, overlap_size: int = 64) -> List[str]:
    """
    Splits text into chunks of roughly `chunk_size` words,
    with an overlap of roughly `overlap_size` words.
    Respects sentence boundaries so thoughts are not cut mid-sentence.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap_size < 0 or overlap_size >= chunk_size:
        raise ValueError("overlap_size must be non-negative and smaller than chunk_size")
    sentences = split_into_sentences(text)

    chunks = []
    current_chunk_sentences = []
    current_word_count = 0

    for sentence in sentences:
        sentence_word_count = get_word_count(sentence)

        # If adding the next sentence exceeds chunk_size, finalize the chunk
        if current_word_count + sentence_word_count > chunk_size and current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))

            # Start the new chunk with the overlap
            overlap_sentences = []
            overlap_word_count = 0

            # Traverse backwards to gather overlap sentences
            for prev_sentence in reversed(current_chunk_sentences):
                prev_word_count = get_word_count(prev_sentence)
                if overlap_word_count + prev_word_count <= overlap_size:
                    overlap_sentences.insert(0, prev_sentence)
                    overlap_word_count += prev_word_count
                else:
                    # Ensure at least one sentence overlaps if the last sentence is huge
                    if not overlap_sentences:
                        overlap_sentences.insert(0, prev_sentence)
                        overlap_word_count += prev_word_count
                    break

            current_chunk_sentences = overlap_sentences
            current_word_count = overlap_word_count

        current_chunk_sentences.append(sentence)
        current_word_count += sentence_word_count

    # Add the last remaining chunk
    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))

    return chunks
