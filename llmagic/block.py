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
        # Initialize the Block with various parameters including children, text, name, etc.
        self._initialize_basic_properties(
            children,
            text,
            name,
            max_tokens,
            truncate,
            separator,
            ellipsis,
            tokenizer,
            boundary,
        )
        # If a separator is specified and there are children, insert a separator TextBlock between each child
        self._insert_separators()

        # If text is provided, create a TextBlock from it and prepend it to the children
        self._prepend_text_block(text)

        # validate children with truncate == "never" max_tokens < self.max_token
        self._validate_children_max_tokens()


    def _initialize_basic_properties(
        self,
        children,
        text,
        name,
        max_tokens,
        truncate,
        separator,
        ellipsis,
        tokenizer,
        boundary,
    ):
        """
        Initializes the basic properties of the Block.
        """
        self.name = name
        self.max_tokens = max_tokens
        self.truncation_strategy = truncate
        self.separator = separator
        self.ellipsis = ellipsis
        self._tokenizer = tokenizer
        self.boundary = boundary

        # Initialize children to an empty list if None is passed
        self.children = children if children is not None else []

        # Validation for max_tokens
        if self.max_tokens is not None and self.max_tokens < 0:
            raise ValueError(
                f"max_tokens should be a positive integer, not {self.max_tokens}"
            )

    def _insert_separators(self):
        if self.separator and self.children:
            # Add separator object between each child
            children_with_separators = []
            for i, child in enumerate(self.children[:-1]):
                children_with_separators.append(child)
                # Add a separator after each child except the last one
                children_with_separators.append(
                    TextBlock(text=self.separator, name="separator")
                )
            children_with_separators.append(self.children[-1])
            self.children = children_with_separators

    def _prepend_text_block(self, text:str):
        if text is not None:
            prepend = [TextBlock(text=text)]
            # If there are already children and a separator is defined, add a separator TextBlock after the new text block
            if self.separator and self.children:
                prepend.append(TextBlock(text=self.separator, name="separator"))
            self.children = prepend + self.children

    def _validate_children_max_tokens(self):
        # Only proceed if the parent has a max_tokens limit set
        if self.max_tokens is None:
            return

        total_tokens_count: int = sum(
            child.max_tokens
            for child in self.children
            if child.truncation_strategy == "never" and child.max_tokens is not None
        )

        # Check if any child's max_tokens exceed the parent's max_tokens
        for child in self.children:
            if child.truncation_strategy == "never" and child.max_tokens is not None:
                if child.max_tokens > self.max_tokens:
                    raise ValueError(
                        f"Child '{child.name}' has max_tokens ({child.max_tokens}) "
                        f"exceeding the parent's max_tokens ({self.max_tokens})."
                    )

        # Check if the total tokens of all children exceed the parent's max_tokens
        if total_tokens_count > self.max_tokens:
            raise ValueError(
                "Total max_tokens of children with 'never' truncation strategy "
                f"({total_tokens_count}) exceeds the parent's max_tokens ({self.max_tokens})."
            )

    def boundary_points(self):
        return find_boundary_points(
            encoding=self.full_tokens(),
            tokenizer=self._tokenizer,
            boundary=self.boundary,
            truncate=self.truncation_strategy,
        )

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
        for child in self.children:
            if child.truncation_strategy == "never":
                joined_tokens.append(child.full_tokens())
            else:
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
            child_tokens = child.tokens().ids

            if child.truncation_strategy == "never":
                rich_texts.append(child.rich_text())

            elif max_tokens is None or (tokens_seen + len(child_tokens) < max_tokens):
                # We can add this child and have tokens left over
                rich_texts.append(child.rich_text())
                tokens_seen += len(child_tokens)
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

    def __getitem__(self, key) -> AbstractBlock:
        if isinstance(key, str):
            for child in self.children:
                if child.name == key:
                    return child

            raise KeyError(f"Key {key} not found in Block")

        return self.children[key]

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
        return find_boundary_points(
            encoding=self.full_tokens(),
            tokenizer=self._tokenizer,
            boundary=self.boundary,
            truncate=self.truncation_strategy,
        )

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

        display_text = Text()

        if truncation_strategy == "never":
            full_text = self._tokenizer.decode(self.full_tokens().ids)
            display_text = Text(full_text)

        else:
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
        if self.truncation_strategy == "never":
            return self.full_tokens()

        else:
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
