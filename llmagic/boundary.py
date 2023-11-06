from llmagic.dtypes import Boundary
import spacy

nlp = spacy.load("en_core_web_sm")


def get_offsets(words: list[str]) -> list[tuple[int]]:
    start_offset = 0
    result: list[tuple[int]] = []
    
    for word in words:
        start: int = start_offset
        end: int = start + len(word)
        result.append((start, end))
        start_offset = end + 1
    return result


def find_boundary_points(encoding, tokenizer, boundary: Boundary) -> list[int]:
    """
    Return token indices that correspond to valid boundary points
    """
    boundary_points: list[int] = []
    if boundary == "token":
        return list(range(len(encoding.ids)))
    elif boundary == "line":
        boundary_token = tokenizer.encode("\n").ids[0]
        print(boundary_points)
        boundary_points.extend(
            [i for i, token in enumerate(encoding.ids) if token == boundary_token]
        )
    elif boundary == "whitespace":
        whitespace_token = "Ġ"
        boundary_points.extend(
            [
                i
                for i, token in enumerate(encoding.tokens)
                if token.startswith(whitespace_token)
            ]
        )

    elif boundary == "sentence":
        decoded_text = tokenizer.decode(encoding.ids)
        doc = nlp(decoded_text)
        token_words = []

        for token in encoding.tokens:
            if token.startswith("Ġ"):
                token_words.append(token.replace("Ġ", ""))
            else:
                token_words.append(token)

        sentence_words = [word for sentence in doc.sents for word in sentence]
        char_offsets = get_offsets(sentence_words)
        print("character offsets", char_offsets)
        for char_offset in char_offsets:
            char_start, char_end = char_offset
            
            token_offsets = get_offsets(words)
            for idx, token_offset in enumerate(token_offsets):
                token_start, token_end = token_offset
                if token_start <= char_start < token_end:
                    boundary_points.append(idx)
            print("token offsets", token_offsets)
        
    else:
        raise NotImplementedError(f"Boundary {boundary} not implemented")
    return boundary_points
