from abc import ABC, abstractmethod
from typing import Callable, Literal

from rich.console import Group
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from tokenizers import Encoding

from llmagic.boundary import find_boundary_points
from llmagic.dtypes import Boundary, TruncationStrategy
from llmagic.truncation import truncate


class AbstractBlock(ABC):
    @abstractmethod
    def full_tokens(self) -> Encoding:
        pass

    @abstractmethod
    def full_text(self) -> str:
        pass

    @abstractmethod
    def tokens(self) -> Encoding:
        pass

    @abstractmethod
    def rich_text(self, max_tokens: int | None = None) -> Panel:
        pass

    @abstractmethod
    def text(self) -> str:
        pass

    def full_size(self):
        return len(self.full_tokens().tokens)

    def size(self):
        return len(self.tokens().tokens)

    @abstractmethod
    def set_tokenizer(self, tokenizer):
        pass


class Block(AbstractBlock):
    def __init__(
        self,
        children: list[AbstractBlock] | None = None,
        text: str | None = None,
        name: str | None = None,
        max_tokens: int | None = None,
        truncate: TruncationStrategy = "right",
        separator: str = "",
        ellipsis: bool = False,
        tokenizer: any = None,
        boundary: Boundary = "token",
    ):
        self.name = name
        self.max_tokens = max_tokens
        self.truncation_strategy: TruncationStrategy = truncate
        self.children = children if children is not None else []
        self.ellipsis = ellipsis
        # TODO: make tokenizer configurable
        self.separator = separator
        self._tokenizer = tokenizer
        self.boundary = boundary

        if self.separator and self.children:
            # Add separator object between each child
            children_with_separators = []
            for i, child in enumerate(self.children[:-1]):
                children_with_separators.append(child)
                children_with_separators.append(
                    TextBlock(text=self.separator, name="separator")
                )
            children_with_separators.append(self.children[-1])
            self.children = children_with_separators

        if text is not None:
            prepend = [TextBlock(text=text)]
            if self.separator and self.children:
                prepend.append(TextBlock(text=self.separator, name="separator"))
            self.children = prepend + self.children

        if self.max_tokens is None:
            pass
        elif self.max_tokens < 0:
            raise ValueError(
                f"max_tokens should be a positive integer and not {self.max_tokens}"
            )

    def boundary_points(self):
        return find_boundary_points(self.full_tokens(), self._tokenizer, self.boundary)

    def _ensure_tokenizer_set(self):
        if self._tokenizer is None:
            raise ValueError("Tokenizer must be explicitly provided")
        self.set_tokenizer(self._tokenizer)

    def set_tokenizer(self, tokenizer):
        self._tokenizer = tokenizer
        for child in self.children:
            child.set_tokenizer(tokenizer=tokenizer)

    def full_tokens(self) -> Encoding:
        self._ensure_tokenizer_set()
        joined_tokens: list[Encoding] = []
        for _, child in enumerate(self.children):
            joined_tokens.append(child.full_tokens())
        return Encoding.merge(joined_tokens)

    def full_text(self) -> str:
        self._ensure_tokenizer_set()
        return self._tokenizer.decode(self.full_tokens().ids)

    def tokens(self) -> Encoding:
        self._ensure_tokenizer_set()
        joined_tokens: list[Encoding] = []
        for _, child in enumerate(self.children):
            joined_tokens.append(child.tokens())

        joined: Encoding = Encoding.merge(joined_tokens)

        return truncate(
            joined,
            max_tokens=self.max_tokens,
            truncation_strategy=self.truncation_strategy,
            ellipsis=self.ellipsis,
            tokenizer=self._tokenizer,
            boundary_points=self.boundary_points(),
        )["tokens"]

    def rich_text(
        self,
        max_tokens: int | None = None,
        truncation_strategy: TruncationStrategy | None = None,
    ) -> Panel:
        self._ensure_tokenizer_set()
        if max_tokens is None:
            max_tokens = self.max_tokens
        if truncation_strategy is None:
            truncation_strategy = self.truncation_strategy

        rich_texts = []
        tokens_seen = 0

        for child in self.children:
            if (
                max_tokens is None
                or (tokens_seen + len(child.tokens().ids)) < max_tokens
            ):
                # We can add this child and have tokens left over
                rich_texts.append(child.rich_text())
                tokens_seen += len(child.tokens().ids)
            else:
                # We exceed the max tokens amount
                number_allowed = max(max_tokens - tokens_seen, 0)
                rich_texts.append(
                    child.rich_text(
                        max_tokens=number_allowed,
                        truncation_strategy=truncation_strategy,
                    )
                )
                tokens_seen += number_allowed
        return Panel(
            Group(*rich_texts),
            title=self.name or "",
            title_align="left",
            border_style=f"bold blue",
        )

    def text(self) -> str:
        self._ensure_tokenizer_set()
        return self._tokenizer.decode(self.tokens().ids)

    def __repr__(self):
        return f'<Block name="{self.name}" size=[{self.full_size()}/{self.max_tokens or "inf"}] text="{self.text()[:25] + "..."}">'

    def append(self, other: AbstractBlock | str):
        self.__add__(other)

    def __add__(self, other: AbstractBlock | str):
        if isinstance(other, str):
            if self.separator and self.children:
                self.children.append(TextBlock(text=self.separator, name="separator"))
            self.children.append(TextBlock(text=other, ellipsis=self.ellipsis))
            return self
        elif isinstance(other, AbstractBlock):
            if self.separator and self.children:
                self.children.append(TextBlock(text=self.separator, name="separator"))
            self.children.append(other)
            return self
        else:
            raise TypeError(f"Cannot add type {type(other)} to Block")

    def __len__(self):
        return len(self.full_text())

    def by_name(self):
        pass

    def by_class(self):
        pass

    def __del__(self):
        pass


# class SectionBlock(Block):
#     def __init__(
#         self,
#         header: str,
#         children: list[AbstractBlock] | None = None,
#         text: str | None = None,
#         name: str | None = None,
#         max_tokens: int | None = None,
#         truncate: TruncationStrategy = "right",
#         separator: str = "",
#     ):
#         if children is None:
#             children = []

#         if text is not None:
#             children = [TextBlock(text=text)] + children

#         if header is not None:
#             if not header.endswith("\n"):
#                 header = header + "\n"
#             children = [TextBlock(text=header, name="header")] + children

#         super().__init__(
#             children=children,
#             text=None,
#             name=name,
#             max_tokens=max_tokens,
#             truncate=truncate,
#             separator=separator,
#         )


class QueueBlock(Block):
    def __init__(self, queue_size: int = 32, **kwargs):
        super().__init__(**kwargs)
        self.queue_size = queue_size
        self.children = self.children[-queue_size:]

    def add(self, other: AbstractBlock | str):
        if len(self.children) >= self.queue_size:
            self.children.pop(0)
        self.__add__(other)


class TextBlock(AbstractBlock):
    def __init__(
        self,
        text: str,
        max_value: int | None = 3,
        name: str | None = None,
        max_tokens: int | None = None,
        truncate: TruncationStrategy = "right",
        ellipsis: bool = False,
        tokenizer: any = None,
        boundary: Boundary = "token",
    ):
        self._text = text
        self._tokenizer = tokenizer
        self._tokens = None
        self.name = name
        self.max_tokens = max_tokens
        self.truncation_strategy: TruncationStrategy = truncate
        self.max_value = max_value
        self.ellipsis = ellipsis
        self.boundary = boundary

    def boundary_points(self):
        return find_boundary_points(self.full_tokens(), self._tokenizer, self.boundary)

    def set_tokenizer(self, tokenizer):
        self._tokenizer = tokenizer

    def rich_text(
        self,
        max_tokens: int | None = None,
        truncation_strategy: TruncationStrategy | None = None,
    ) -> Panel:
        if max_tokens is None:
            max_tokens = self.max_tokens
        if truncation_strategy is None:
            truncation_strategy = self.truncation_strategy

        child_truncated_tokens: Encoding = truncate(
            self.full_tokens(),
            max_tokens=self.max_tokens,
            truncation_strategy=self.truncation_strategy,
            tokenizer=self._tokenizer,
        )
        parent_truncated_tokens: Encoding = truncate(
            child_truncated_tokens["tokens"],
            max_tokens=max_tokens,
            truncation_strategy=truncation_strategy,
            tokenizer=self._tokenizer,
        )

        left_text = self._tokenizer.decode(
            Encoding.merge(
                [
                    child_truncated_tokens["remainder_left"],
                    parent_truncated_tokens["remainder_left"],
                ]
            ).ids
        )
        right_text = self._tokenizer.decode(
            Encoding.merge(
                [
                    parent_truncated_tokens["remainder_right"],
                    child_truncated_tokens["remainder_right"],
                ]
            ).ids
        )
        inner_text = self._tokenizer.decode(parent_truncated_tokens["tokens"].ids)

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

    def full_text(self) -> str:
        return self._text

    def full_tokens(self) -> Encoding:
        if self._tokens == None:
            if self._tokenizer is None:
                raise ValueError("Tokenizer must be explicitly provided")
            self._tokens = self._tokenizer.encode(self.full_text())
        return self._tokens

    def text(self) -> str:
        return self._tokenizer.decode(self.tokens().ids)

    def tokens(self) -> Encoding:
        truncated = truncate(
            self.full_tokens(),
            max_tokens=self.max_tokens,
            truncation_strategy=self.truncation_strategy,
            ellipsis=self.ellipsis,
            tokenizer=self._tokenizer,
            boundary_points=self.boundary_points(),
        )
        return truncated["tokens"]

    def __repr__(self):
        return f'<Block name="{self.name}" size=[{self.full_size()}/{self.max_tokens or "inf"}] text="{self.text()[:25] + "..."}">'
