from typing import Any
from llmagic.dtypes import Boundary, TruncationStrategy

class SpacyPlugin:
    def __init__(self):
        self.nlp = None
        
    @property
    def sentence_splitter(self):
        import spacy

        if self.nlp is None:
            self.nlp = spacy.blank("en")
            self.nlp.add_pipe("sentencizer")
        return self.nlp

class BatchedSpacyPlugin:
    def __init__(self, batch_size=100):
        self._nlp = None
        self.batch_size = batch_size

    @property
    def nlp(self):
        if self._nlp is None:
            import spacy
            self._nlp = spacy.blank("en")
            self._nlp.add_pipe("sentencizer")
        return self._nlp

    def sentence_splitter(self, texts):
        for doc in self.nlp.pipe(texts, batch_size=self.batch_size):
            return doc


SPACY_MODEL = SpacyPlugin()
BATCHED_SPACY_MODEL = BatchedSpacyPlugin()

# @profile
def find_boundary_points(
    encoding, tokenizer, boundary: Boundary, truncate: TruncationStrategy
) -> list[int]:
    """
    Return token indices that correspond to valid boundary points
    """
    boundary_points: list[int] = []
    if boundary == "token":
        return list(range(len(encoding.ids)))
    elif boundary == "line":
        boundary_token = tokenizer.encode("\n").ids[0]
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

    # elif boundary == "sentence":
    #     decoded_text = tokenizer.decode(encoding.ids)

    #     doc = BATCHED_SPACY_MODEL.sentence_splitter(decoded_text)

    #     search_start_idx = 0
    #     for sentence in doc.sents:
    #         for offset_idx, (token_char_start, token_char_end) in enumerate(
    #             encoding.offsets[search_start_idx:]
    #         ):
    #             token_idx = search_start_idx + offset_idx

    #             if truncate == "right":
    #                 if token_char_start <= sentence.start_char <= token_char_end:
    #                     boundary_points.append(token_idx)
    #                     search_start_idx = token_idx
    #                     break
    #             elif truncate == "left":
    #                 if token_char_start <= sentence.end_char <= token_char_end:
    #                     boundary_points.append(token_idx)
    #                     search_start_idx = token_idx
    #                     break

    elif boundary == "sentence":
        decoded_text = tokenizer.decode(encoding.ids)
        doc = BATCHED_SPACY_MODEL.sentence_splitter(decoded_text)
        # Pre-compute sentence boundaries
        sentence_boundaries = [
            (sentence.start_char, sentence.end_char) for sentence in doc.sents
        ]

        sentence_idx = 0

        # Iterate through each offset only once
        for offset_idx, (token_char_start, token_char_end) in enumerate(
            encoding.offsets
        ):
            # exit loop if all sentences have been processed
            if sentence_idx >= len(sentence_boundaries):
                break  # All sentences processed

            start_char, end_char = sentence_boundaries[sentence_idx]

            # For 'right' truncation, check against sentence start
            if truncate == "right" and token_char_start <= start_char <= token_char_end:
                boundary_points.append(offset_idx)
                sentence_idx += 1
            # For 'left' truncation, check against sentence end
            if truncate == "left" and token_char_start <= end_char <= token_char_end:
                boundary_points.append(offset_idx)
                sentence_idx += 1
    else:
        raise NotImplementedError(f"Boundary {boundary} not implemented")
    return boundary_points
