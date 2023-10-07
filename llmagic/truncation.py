from llmagic.types import TruncationStrategy


def truncate(
    tokens: list[int], max_tokens: int | None, truncation_strategy: TruncationStrategy
) -> dict[str, list[int]]:
    size = len(tokens)
    remainder_right = []
    remainder_left = []
    if max_tokens is not None and size > max_tokens:
        match truncation_strategy:
            case "right":
                remainder_right = tokens[max_tokens:]
                tokens = tokens[:max_tokens]
            case "left":
                remainder_left = tokens[:-max_tokens]
                tokens = tokens[-max_tokens:]
            case _:
                # No truncation
                pass
    return {
        "remainder_left": remainder_left,
        "remainder_right": remainder_right,
        "tokens": tokens,
    }
