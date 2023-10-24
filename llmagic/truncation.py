from typing import Callable

from tokenizers import Encoding
from llmagic.dtypes import TruncationStrategy
from llmagic.tokenizer import create_tokenizer


def truncate(
    tokens: Encoding,
    max_tokens: int | None,
    truncation_strategy: TruncationStrategy,
    tokenizer: Callable,
    ellipsis: bool = False,
) -> dict[str, Encoding]:
    size = len(tokens.ids)
    remainder_right = []
    remainder_left = []
    ellipsis_tokens: Encoding = tokenizer.encode("...")
    n_ellipsis_tokens: int = len(ellipsis_tokens.ids)
    if max_tokens is not None and size > max_tokens:
        cutoff = size - max_tokens
        match truncation_strategy:
            case "right":
                remainder_right = tokens.truncate(cutoff, direction="left")
                tokens = tokens.truncate(max_tokens, direction="right")
            case "left":
                remainder_left = tokens.truncate(cutoff, direction="right")
                tokens = tokens.truncate(max_tokens, direction="left")
            case _:
                # No truncation
                pass
    return {
        "remainder_left": remainder_left,
        "remainder_right": remainder_right,
        "tokens": tokens,
    }


def trim_to_boundary():
    # look up functions that chunk texts given certain contexts
    pass
