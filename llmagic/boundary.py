from llmagic.dtypes import Boundary
import spacy

nlp = spacy.load("en_core_web_sm")


def find_boundary_points(encoding, tokenizer, boundary: Boundary) -> list[int]:
    """
    Return token indices that correspond to valid boundary points
    """
    boundary_points: list = []
    if boundary == "token":
        return list(range(len(encoding.ids)))
    elif boundary == "line":
        boundary_token = tokenizer.encode("\n").ids[0]
        boundary_points.extend([
            i for i, token in enumerate(encoding.ids) if token == boundary_token
        ])
    elif boundary == "whitespace":
        whitespace_token = tokenizer.encode("\t").ids[0] or tokenizer.encode(" ").ids[0]
        print("WHITESPACE TOKEN", whitespace_token)
        print("ENCODING IDS", encoding.ids)
        print("TEXT", tokenizer.decode(encoding.ids))

        decode = tokenizer.decode(encoding.ids).split()
        tok_map = {}
        for ids, tok in zip(encoding.ids, decode):
            tok_map[ids] = tok
        print(tok_map)

        boundary_points.extend([
            i for i, token in enumerate(encoding.ids) if token == whitespace_token
        ])

    elif boundary == "sentence":
        decoded_text = tokenizer.decode(encoding.ids)
        doc = nlp(decoded_text)
        for sent in doc.sents:
            start = sent[0].i
            end = sent[-1].i
            boundary_points.append(start)
            boundary_points.append(end)

    else:
        raise NotImplementedError(f"Boundary {boundary} not implemented")
    return boundary_points
