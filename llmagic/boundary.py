from llmagic.dtypes import Boundary
import spacy

nlp = spacy.load("en_core_web_sm")

def get_offsets(words:list[str]) -> list[tuple[int]]:
    start_offset = 0
    result: list[tuple[int]] = []
    for word in words:
        # text:str = word.text 
        start:int = start_offset
        end:int = start + len(word)
        result.append((start, end))
        start_offset = end
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
        start_offset: int = 0
        words = []
        
        for token in encoding.tokens:
            if token.startswith("Ġ"):
                words.append(token.replace("Ġ", ""))
            else:
                words.append(token)

        for sent in doc.sents:
            # Get the start and end index of a sentence in sentences
            for word in sent:
                text: str = word.text
                char_start: int = start_offset
                char_end: int = char_start + len(text)
                print('char offsets', (char_start, char_end))
                # for idx, offset in enumerate(encoding.offsets):
                #     start, end = offset
                #     if start <= char_start < end:
                #         boundary_points.append(idx)
                # start_offset = char_end
                
                offsets = get_offsets(words)
                for idx, offset in enumerate(offsets):
                    token_start, token_end = offset
                    if token_start <= char_start < token_end:
                        boundary_points.append(idx)
                print("token offsets", offsets)
                start_offset = char_end
    else:
        raise NotImplementedError(f"Boundary {boundary} not implemented")
    return boundary_points
