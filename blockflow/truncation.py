import copy
from typing import Callable

from tokenizers import Encoding

from blockflow.dtypes import TruncationStrategy
from blockflow.errors import TruncationError
import warnings


def truncate_encoding(self, *args, **kwargs):
    copied = copy.deepcopy(self)
    copied.truncate(*args, **kwargs)
    return copied


def add_ellipsis_token(tokens, ellipsis_token, direction="right"):
    n_ellipsis_tokens = len(ellipsis_token.ids)
    num_tokens_to_keep = max(0, len(tokens.ids) - n_ellipsis_tokens)
    if num_tokens_to_keep > 0:
        if direction == "left":
            first_tokens_removed = truncate_encoding(
                tokens, num_tokens_to_keep, direction="left"
            )
            tokens = Encoding.merge([ellipsis_token, first_tokens_removed])
        elif direction == "right":
            last_tokens_removed = truncate_encoding(
                tokens, num_tokens_to_keep, direction="right"
            )
            tokens = Encoding.merge([last_tokens_removed, ellipsis_token])

    return tokens


def process_boundary_points(
    boundary_points: list[int],
    max_tokens: int,
    token_size: int = None,
    direction="right",
) -> int:
    if boundary_points is not None:
        if direction == "left":
            while (
                token_size - max_tokens - 1
            ) not in boundary_points and max_tokens > 0:
                # -------------x-
                max_tokens -= 1
        elif direction == "right":
            while max_tokens not in boundary_points and max_tokens > 0:
                max_tokens -= 1

    return max_tokens


def truncate(
    tokens: Encoding,
    max_tokens: int | None,
    truncation_strategy: TruncationStrategy,
    tokenizer: Callable,
    ellipsis: bool = False,
    boundary_points: list[int] | None = None,
    boundary_name: str = None,
) -> dict[str, Encoding]:
    token_size = len(tokens.ids)
    remainder_right = Encoding()
    remainder_left = Encoding()
    ellipsis_tokens: Encoding = tokenizer.encode("...")
    # n_ellipsis_tokens: int = len(ellipsis_tokens.ids)
    if max_tokens is not None and token_size > max_tokens:
        match truncation_strategy:
            case "right":
                processed_max_tokens = process_boundary_points(
                    boundary_points, max_tokens, direction="right"
                )
                cutoff = token_size - processed_max_tokens
                remainder_right = truncate_encoding(tokens, cutoff, direction="left")
                tokens = truncate_encoding(
                    tokens, processed_max_tokens, direction="right"
                )
                if ellipsis:
                    tokens = add_ellipsis_token(
                        tokens, ellipsis_token=ellipsis_tokens, direction="right"
                    )
            case "left":
                processed_max_tokens = process_boundary_points(
                    boundary_points, max_tokens, token_size, direction="left"
                )
                cutoff = token_size - processed_max_tokens
                remainder_left = truncate_encoding(tokens, cutoff, direction="right")
                tokens = truncate_encoding(
                    tokens, processed_max_tokens, direction="left"
                )
                if ellipsis:
                    tokens = add_ellipsis_token(
                        tokens, ellipsis_token=ellipsis_tokens, direction="left"
                    )

            case "never":
                if token_size > max_tokens:
                    raise TruncationError(
                        f"Cannot truncate to {max_tokens} tokens when truncate is 'never'."
                    )

            case _:
                # No truncation
                pass

        if len(tokens.ids) == 0:
            warnings.warn(
                f"Truncated Text is empty. Consider using a different boundary setting other than '{boundary_name}'"
            )

    return {
        "remainder_left": remainder_left,
        "remainder_right": remainder_right,
        "tokens": tokens,
    }
