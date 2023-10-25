import copy
from typing import Callable

from tokenizers import Encoding

from llmagic.dtypes import TruncationStrategy
from llmagic.tokenizer import create_tokenizer


def truncate_encoding(self, *args, **kwargs):
    copied = copy.deepcopy(self)
    copied.truncate(*args, **kwargs)
    return copied


def truncate(
    tokens: Encoding,
    max_tokens: int | None,
    truncation_strategy: TruncationStrategy,
    tokenizer: Callable,
    ellipsis: bool = False,
    boundary_points: list[int] | None = None,
) -> dict[str, Encoding]:
    size = len(tokens.ids)
    remainder_right = Encoding()
    remainder_left = Encoding()
    ellipsis_tokens: Encoding = tokenizer.encode("...")
    n_ellipsis_tokens: int = len(ellipsis_tokens.ids)
    if max_tokens is not None and size > max_tokens:
        match truncation_strategy:
            case "right":
                # Factor this out into a function
                if boundary_points is not None:
                    while max_tokens not in boundary_points and max_tokens > 0:
                        max_tokens -= 1

                cutoff = size - max_tokens
                remainder_right = truncate_encoding(tokens, cutoff, direction="left")
                tokens = truncate_encoding(tokens, max_tokens, direction="right")
                if ellipsis:
                    # Factor out
                    num_tokens_to_keep = max(0, len(tokens.ids) - n_ellipsis_tokens)
                    if num_tokens_to_keep > 0:
                        last_tokens_removed = truncate_encoding(
                            tokens, num_tokens_to_keep, direction="right"
                        )
                        tokens = Encoding.merge([last_tokens_removed, ellipsis_tokens])
            case "left":
                # Factor out
                if boundary_points is not None:
                    while (size - max_tokens - 1) not in boundary_points and (
                        size - max_tokens - 1
                    ) > 0:
                        max_tokens -= 1

                cutoff = size - max_tokens
                remainder_left = truncate_encoding(tokens, cutoff, direction="right")
                tokens = truncate_encoding(tokens, max_tokens, direction="left")
                if ellipsis:
                    # Factor out
                    num_tokens_to_keep = max(0, len(tokens.ids) - n_ellipsis_tokens)
                    if num_tokens_to_keep > 0:
                        first_tokens_removed = truncate_encoding(
                            tokens, num_tokens_to_keep, direction="left"
                        )
                        tokens = Encoding.merge([ellipsis_tokens, first_tokens_removed])
            case _:
                # No truncation
                pass
    return {
        "remainder_left": remainder_left,
        "remainder_right": remainder_right,
        "tokens": tokens,
    }
