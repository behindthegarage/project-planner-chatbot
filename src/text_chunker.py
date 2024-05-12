import tiktoken

def tokenize_text(text, encoding_name="cl100k_base"):
    """Tokenize text using the specified encoding."""
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    return tokens

def chunk_text(tokens, max_tokens=2048):
    """Chunk tokenized text into segments with a maximum token count."""
    chunks = []
    current_chunk = []
    current_length = 0

    for token in tokens:
        if current_length + 1 > max_tokens:
            chunks.append(current_chunk)
            current_chunk = []
            current_length = 0
        current_chunk.append(token)
        current_length += 1

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def decode_tokens(tokens, encoding_name="cl100k_base"):
    """Decode tokens back to text using the specified encoding."""
    encoding = tiktoken.get_encoding(encoding_name)
    text = encoding.decode(tokens)
    return text
