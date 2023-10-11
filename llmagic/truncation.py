from llmagic.types import TruncationStrategy
from llmagic.tokenizer import tokenizer


def truncate(
    tokens: list[int],
    max_tokens: int | None,
    truncation_strategy: TruncationStrategy,
    ellipsis: bool = False,
) -> dict[str, list[int]]:
    size = len(tokens)
    remainder_right = []
    remainder_left = []
    ellipsis_tokens = tokenizer.encode("...")
    n_ellipsis_tokens = len(ellipsis_tokens)
    if max_tokens is not None and size > max_tokens:
        match truncation_strategy:
            case "right":
                remainder_right = tokens[max_tokens:]
                tokens = tokens[:max_tokens]
                if ellipsis:
                    for i in range(n_ellipsis_tokens):
                        offset = max_tokens - n_ellipsis_tokens + i
                        if 0 <= offset < len(tokens):
                            tokens[offset] = ellipsis_tokens[i]
            case "left":
                cutoff = size - max_tokens
                remainder_left = tokens[:cutoff]
                tokens = tokens[cutoff:]
                if ellipsis:
                    for i in range(n_ellipsis_tokens):
                        if 0 <= i < len(tokens):
                            tokens[i] = ellipsis_tokens[i]
            case _:
                # No truncation
                pass
    return {
        "remainder_left": remainder_left,
        "remainder_right": remainder_right,
        "tokens": tokens,
    }


def trim_to_boundary():
    pass
