from llmagic.tokenizer import tokenizer
from rich.panel import Panel
from rich.console import Group
from rich.style import Style
from rich.text import Text
from abc import ABC, abstractmethod

from llmagic.types import TruncationStrategy
from llmagic.truncation import truncate


class AbstractBlock(ABC):
    @property
    @abstractmethod
    def full_tokens(self) -> list[int]:
        pass

    @property
    @abstractmethod
    def full_text(self) -> str:
        pass

    @property
    @abstractmethod
    def tokens(self) -> list[int]:
        pass

    @property
    @abstractmethod
    def rich_text(self) -> Panel:
        pass

    @property
    def text(self) -> str:
        return tokenizer.decode(self.tokens)

    @property
    def full_size(self):
        return len(self.full_tokens)

    @property
    def size(self):
        return len(self.tokens)


class Block(AbstractBlock):
    def __init__(
        self,
        text: str | None = None,
        children: list[AbstractBlock] | None = None,
        name: str | None = None,
        max_tokens: int | None = None,
        truncate: TruncationStrategy = "right",
        separator: str = "",
    ):
        self.name = name
        self.max_tokens = max_tokens
        self.truncation_strategy: TruncationStrategy = truncate
        self.children = children if children is not None else []

        if text is not None:
            self.children = [TextBlock(text=text)] + self.children

        # TODO: make tokenizer configurable
        self._separator = separator
        self._separator_tokens = tokenizer.encode(separator)

        if self.max_tokens is None:
            pass
        elif self.max_tokens < 0:
            raise ValueError(
                f"max_tokens should be a positive integer and not {self.max_tokens}"
            )

    @property
    def full_tokens(self) -> list[int]:
        joined_tokens: list[int] = []
        for i, child in enumerate(self.children):
            if i > 0:
                joined_tokens += self._separator_tokens
            joined_tokens += child.full_tokens
        return joined_tokens

    @property
    def full_text(self) -> str:
        return tokenizer.decode(self.full_tokens)

    @property
    def tokens(self) -> list[int]:
        joined_tokens: list[int] = []
        for i, child in enumerate(self.children):
            if i > 0:
                joined_tokens += self._separator_tokens
            joined_tokens += child.tokens

        return truncate(
            joined_tokens,
            max_tokens=self.max_tokens,
            truncation_strategy=self.truncation_strategy,
        )["tokens"]

    @property
    def rich_text(self) -> Panel:
        return Panel(
            Group(*(child.rich_text for child in self.children)),
            title=self.name or "",
            title_align="left",
            border_style=f"bold blue",
        )

    @property
    def text(self) -> str:
        return tokenizer.decode(self.tokens)

    def __repr__(self):
        return f'<TextBlock size=[{self.full_size}/{self.max_tokens or "inf"}] text="{self.text[:25] + "..."}">'

    def __add__(self, other):
        if isinstance(other, str):
            self.children.append(TextBlock(text=other))
            return self
        elif isinstance(other, AbstractBlock):
            self.children.append(other)
            return self
        else:
            raise TypeError(f"Cannot add type {type(other)} to Block")

    def __len__(self):
        return len(self.full_text)


class TextBlock(AbstractBlock):
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
        self.truncation_strategy: TruncationStrategy = truncate

    @property
    def rich_text(self) -> Panel:
        truncate_tokens = truncate(
            self.full_tokens,
            max_tokens=self.max_tokens,
            truncation_strategy=self.truncation_strategy,
        )
        right_text = tokenizer.decode(truncate_tokens["remainder_right"])
        left_text = tokenizer.decode(truncate_tokens["remainder_left"])
        inner_text = tokenizer.decode(truncate_tokens["tokens"])

        display_text = Text()
        display_text.append(left_text, style="bold magenta")
        display_text.append(inner_text, style="bold blue")
        display_text.append(right_text, style="bold magenta")

        return Panel(
            display_text,
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
        truncated = truncate(
            self.full_tokens,
            max_tokens=self.max_tokens,
            truncation_strategy=self.truncation_strategy,
        )
        return truncated["tokens"]
