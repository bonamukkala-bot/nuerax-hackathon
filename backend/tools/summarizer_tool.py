from typing import Optional
import re


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks for processing.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break

    return chunks


def simple_extractive_summary(text: str, num_sentences: int = 5) -> str:
    """
    Simple extractive summarization without LLM.
    Used as fallback when LLM is not available.
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if not sentences:
        return text[:500]

    if len(sentences) <= num_sentences:
        return " ".join(sentences)

    # Score sentences by position and keyword frequency
    words = text.lower().split()
    word_freq = {}
    for word in words:
        word = re.sub(r'[^\w]', '', word)
        if len(word) > 3:
            word_freq[word] = word_freq.get(word, 0) + 1

    sentence_scores = []
    for i, sentence in enumerate(sentences):
        score = 0
        # Position score — first and last sentences are important
        if i < 3:
            score += 3
        if i >= len(sentences) - 3:
            score += 2

        # Keyword score
        sentence_words = sentence.lower().split()
        for word in sentence_words:
            word = re.sub(r'[^\w]', '', word)
            if word in word_freq:
                score += word_freq[word]

        sentence_scores.append((score, i, sentence))

    # Sort by score, keep top sentences, then re-sort by position
    sentence_scores.sort(key=lambda x: x[0], reverse=True)
    top_sentences = sentence_scores[:num_sentences]
    top_sentences.sort(key=lambda x: x[1])

    summary = " ".join([s[2] for s in top_sentences])
    return summary


def summarize_text(
    text: str,
    max_length: int = 500,
    style: str = "concise"
) -> str:
    """
    Summarize text using extractive summarization.
    style: 'concise', 'detailed', 'bullets'
    """
    if not text or not text.strip():
        return "No text provided for summarization."

    text = text.strip()

    # If text is already short enough
    if len(text) <= max_length:
        return text

    if style == "bullets":
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        top = sentences[:8]
        bullet_points = "\n".join([f"• {s}" for s in top])
        return f"Key points:\n{bullet_points}"

    elif style == "detailed":
        num_sentences = 10
    else:
        num_sentences = 5

    summary = simple_extractive_summary(text, num_sentences)

    if len(summary) > max_length * 2:
        summary = summary[:max_length * 2] + "..."

    return summary


def summarize_document(text: str, title: str = "Document") -> str:
    """
    Create a structured summary of a document.
    """
    if not text.strip():
        return "Empty document."

    word_count = len(text.split())
    char_count = len(text)

    result = []
    result.append(f"DOCUMENT SUMMARY: {title}")
    result.append(f"Length: {word_count} words, {char_count} characters\n")

    # Main summary
    summary = simple_extractive_summary(text, num_sentences=6)
    result.append(f"SUMMARY:\n{summary}\n")

    # Key points
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
    if sentences:
        result.append("KEY SENTENCES:")
        for s in sentences[:5]:
            result.append(f"  • {s}")

    return "\n".join(result)


def run_summarizer_tool(input: str) -> str:
    """
    Main entry point for the summarizer tool.
    Input should be the text to summarize.
    """
    input = input.strip()

    if not input:
        return "No text provided to summarize."

    # Check if it references an uploaded file
    from tools.file_reader_tool import _uploaded_files, read_file

    if input in _uploaded_files:
        file_info = _uploaded_files[input]
        text = read_file(file_info["path"], file_info["name"])
        return summarize_document(text, file_info["name"])

    # Check by filename
    for file_id, info in _uploaded_files.items():
        if info["name"].lower() == input.lower():
            text = read_file(info["path"], info["name"])
            return summarize_document(text, info["name"])

    # Otherwise summarize the input text directly
    if len(input) > 100:
        return summarize_document(input)

    return f"Text too short to summarize: {input}"