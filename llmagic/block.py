from llmagic.tokenizer import tokenizer
from typing import NoReturn
import typing
from rich.panel import Panel
from rich.console import Group

TruncationStrategy = typing.Literal["left", "right"]


class Block:
    def __init__(
        self,
        text: str | None = None,
        children: list["Block"] | None = None,
        name: str | None = None,
        max_tokens: int | None = None,
        truncate: TruncationStrategy = "right",
        separator: str = "",
    ):
        self.name = name
        self.max_tokens = max_tokens
        self.truncatation_strategy = truncate
        self.children = children if children is not None else []

        # Prepend raw text
        if text is not None:
            self.children = [TextBlock(text=text)] + self.children

        # TODO: make tokenizer configurable
        self._separator = separator
        self._separator_tokens = tokenizer.encode(separator)

    @property
    def full_text(self) -> str:
        return tokenizer.decode(self.full_tokens)

    @property
    def full_tokens(self) -> list[int]:
        joined_tokens: list[int] = []
        for i, child in enumerate(self.children):
            if i > 0:
                joined_tokens += self._separator_tokens
            joined_tokens += child.full_tokens
        return joined_tokens

    @property
    def tokens(self) -> list[int]:
        joined_tokens: list[int] = []
        for i, child in enumerate(self.children):
            if i > 0:
                joined_tokens += self._separator_tokens
            joined_tokens += child.tokens
        return self._truncate(joined_tokens)

    @property
    def full_size(self):
        return len(self.full_tokens)

    @property
    def size(self):
        return len(self.tokens)

    @property
    def rich_text(self) -> Panel:
        return Panel(
            Group(*(child.rich_text for child in self.children)),
            title=self.name or "",
            title_align="left",
            border_style="bold blue",
        )

    @property
    def text(self) -> str:
        return tokenizer.decode(self.tokens)

    def __repr__(self):
        return f'<TextBlock size=[{self.full_size}/{self.max_tokens or "inf"}] text="{self.text[:25] + "..."}">'

    def _truncate(self, tokens: list[int]) -> list[int] | NoReturn:
        size = len(tokens)
        if self.max_tokens is not None and size > self.max_tokens:
            match self.truncatation_strategy:
                case "right":
                    tokens = tokens[: self.max_tokens]
                case "left":
                    tokens = tokens[-self.max_tokens :]
                case _:
                    # No truncation
                    pass
        return tokens

    def __add__(self, other):
        if isinstance(other, str):
            self.children.append(TextBlock(text=other))
            return self
        elif isinstance(other, Block):
            self.children.append(other)
            return self
        else:
            raise TypeError("Block can only be added to a string")


class TextBlock(Block):
    def __init__(
        self,
        text: str,
        name: str | None = None,
        max_tokens: int | None = None,
        truncate: TruncationStrategy = "right",
    ):
        self._text = text
        self._tokens = tokenizer.encode(text)
        self.name = name
        self.max_tokens = max_tokens
        self.truncatation_strategy = truncate

    @property
    def rich_text(self) -> Panel:
        return Panel(
            self.text,
            title=self.name or "",
            title_align="left",
            border_style="bold green",
        )

    @property
    def full_text(self) -> str:
        return self._text

    @property
    def full_tokens(self) -> list[int]:
        return self._tokens

    @property
    def tokens(self):
        truncated = self._truncate(self._tokens)
        return truncated
