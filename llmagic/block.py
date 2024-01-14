from abc import ABC, abstractmethod
from typing import Callable, Literal

from rich.console import Group
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from tokenizers import Encoding

from llmagic.boundary import find_boundary_points
from llmagic.dtypes import Boundary, TruncationStrategy
from llmagic.tokenizer import create_tokenizer
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
        tokenizer: Callable | None = None,
        boundary: Boundary = "token",
        reading_order_idx: int | None = None,
        priority_order_idx: int | None = None,
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
            reading_order_idx,
            priority_order_idx,
        )
        # If a separator is specified and there are children, insert a separator TextBlock between each child
        self._insert_separators()

        # If text is provided, create a TextBlock from it and prepend it to the children
        self._prepend_text_block(text)

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
        reading_order_idx,
        priority_order_idx,
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
        self.reading_order_idx = reading_order_idx
        self.priority_order_idx = priority_order_idx

        # Initialize children to an empty list if None is passed
        self.children: list[TextBlock | Block] = (
            children if children is not None else []
        )

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

    def _prepend_text_block(self, text: str | None):
        if text is not None:
            prepend = [TextBlock(text=text)]
            # If there are already children and a separator is defined, add a separator TextBlock after the new text block
            if self.separator and self.children:
                prepend.append(TextBlock(text=self.separator, name="separator"))
            self.children = prepend + self.children

    def _validate_children_max_tokens(self, max_tokens, truncation_strategy):
        # Only proceed if the parent has a max_tokens limit set
        if self.max_tokens is None:
            return

        total_tokens_count: int = sum(
            (len(child.tokens().tokens))
            for child in self.children
            if child.truncation_strategy == "never"
        )

        # Check if any child's max_tokens exceed the parent's max_tokens
        for child in self.children:
            if child.truncation_strategy == "never":
                if len(child.tokens().tokens) > self.max_tokens:
                    raise ValueError(
                        f"Child '{child.name}' has {len(child.tokens().tokens)} tokens "
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
        if isinstance(self._tokenizer, str):
            raise ValueError(
                "It looks like you are trying to create a tokenizer using a string, please provide a tokenizer object instead."
            )
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

    def sort_by_priority(self, blocks: list["Block | TextBlock"]):
        # obtain reading order and priority order
        for idx, child in enumerate(blocks):
            child.reading_order_idx = idx
            child.priority_order_idx = (
                0 if child.truncation_strategy == "never" else 1,
                -idx if self.truncation_strategy == "left" else idx,
            )

        # sort children by priority order
        return sorted(blocks, key=lambda x: x.priority_order_idx)

    def sort_by_reading_order(self, blocks: list["Block | TextBlock"]):
        return sorted(blocks, key=lambda x: x.reading_order_idx)

    def truncate(self) -> list[dict[str, Encoding]]:
        # load tokenizer
        self._ensure_tokenizer_set()

        # TODO: is this necessary?
        self._validate_children_max_tokens(
            max_tokens=self.max_tokens, truncation_strategy=self.truncation_strategy
        )

        tokens_seen = 0

        self.children = self.sort_by_priority(self.children)

        for child in self.children:
            child_tokens = child.tokens().ids
            child_result = {"remainder_left": Encoding(), "remainder_right": Encoding()}
            if (
                self.max_tokens is None
                or child.truncation_strategy == "never"
                or (tokens_seen + len(child_tokens) < self.max_tokens)
            ):
                # We can add this child and have tokens left over
                child_result["tokens"] = child.tokens()
                tokens_seen += len(child_tokens)
            else:
                # We exceed the max tokens amount
                number_allowed = max(self.max_tokens - tokens_seen, 0)

                # First allow the child to apply any truncation it is required to
                child_truncated_tokens = child.truncate()

                TODO: we have arrived at a tough spot.  child_truncated_tokens is a list
                # Typically we would want to further truncate the tokens using the parent
                # settings.  However, this relies on having a single Encoding() object to work off of.
                # In this case -- we have a list of [{'remainder_left': Encoding, 'remainder_right': Encoding, 'tokens': Encoding}, ...]
                # We can't just merge this into a single Encoding because that will destroy reading order.
                # We need to instead calculate what would happen if we did merge into a single Encoding, but then apply that across
                # the entire list of objects.
                #
                # Merge list to encoding (but keep track of where each token came from) --> truncate --> reapply to full list
                new_boundary_points = find_boundary_points(
                    child_truncated_tokens["tokens"],
                    tokenizer=self._tokenizer,
                    boundary=self.boundary,
                    truncate=self.truncation_strategy,
                )

                parent_truncated_tokens = truncate(
                    child_truncated_tokens["tokens"],
                    tokenizer=self._tokenizer,
                    max_tokens=number_allowed,
                    truncation_strategy=self.truncation_strategy,
                    boundary_points=new_boundary_points,
                    ellipsis=self.ellipsis,
                    boundary_name=self.boundary,
                )
                child_result["remainder_left"] = Encoding.merge(
                    [
                        child_truncated_tokens["remainder_left"],
                        parent_truncated_tokens["remainder_left"],
                    ]
                )
                child_result["remainder_right"] = Encoding.merge(
                    [
                        parent_truncated_tokens["remainder_right"],
                        child_truncated_tokens["remainder_right"],
                    ]
                )
                child_result["tokens"] = parent_truncated_tokens["tokens"]

        sorted_encodings = sorted(
            zip(self.children, encodings), key=lambda x: x[0].reading_order_idx
        )

        self.children = self.sort_by_reading_order(self.children)

        final_encodings = Encoding.merge(
            [encoding for (_, encoding) in sorted_encodings]
        )

        return final_encodings

    def tokens(self) -> Encoding:
        # load tokenizer
        self._ensure_tokenizer_set()

        # validate children with truncate == "never" max_tokens < self.max_token

        self._validate_children_max_tokens(
            max_tokens=self.max_tokens, truncation_strategy=self.truncation_strategy
        )

        encodings = []
        tokens_seen = 0

        self.children = self.sort_by_priority(self.children)

        for child in self.children:
            child_tokens = child.tokens().ids

            if (
                self.max_tokens is None
                or child.truncation_strategy == "never"
                or (tokens_seen + len(child_tokens) < self.max_tokens)
            ):
                # We can add this child and have tokens left over
                encodings.append(child.tokens())
                tokens_seen += len(child_tokens)
            else:
                # We exceed the max tokens amount
                number_allowed = max(self.max_tokens - tokens_seen, 0)

                # First allow the child to apply any truncation it is required to
                prelim = child.tokens()

                new_boundary_points = find_boundary_points(
                    prelim,
                    tokenizer=self._tokenizer,
                    boundary=self.boundary,
                    truncate=self.truncation_strategy,
                )

                truncated_child = truncate(
                    prelim,
                    tokenizer=self._tokenizer,
                    max_tokens=number_allowed,
                    truncation_strategy=self.truncation_strategy,
                    boundary_points=new_boundary_points,
                    ellipsis=self.ellipsis,
                    boundary_name=self.boundary,
                )["tokens"]

                encodings.append(truncated_child)
                tokens_seen += len(truncated_child.tokens)

        sorted_encodings = sorted(
            zip(self.children, encodings), key=lambda x: x[0].reading_order_idx
        )

        self.children = self.sort_by_reading_order(self.children)

        final_encodings = Encoding.merge(
            [encoding for (_, encoding) in sorted_encodings]
        )

        return final_encodings

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

        self.children = self.sort_by_priority(self.children)

        # process children according to their priority
        for child in self.children:
            child_tokens = child.tokens().ids

            if (
                max_tokens is None
                or child.truncation_strategy == "never"
                or (tokens_seen + len(child_tokens) < max_tokens)
            ):
                # We can add this child and have tokens left over
                rich_texts.append(child.rich_text())
                tokens_seen += len(child_tokens)

            else:
                # We exceed the max tokens amount
                number_allowed = max(max_tokens - tokens_seen, 0)

                # First allow the child to apply any truncation it is required to
                child_truncated_tokens = child.truncate()

                TODO: update this once we fix the truncate function -- this should be super easy
                # to write once we have truncate() working properly with a list return type
                # because the remainder_left and the remainder_right objects are exactly what we need
                # for formatting the rich text
                new_boundary_points = find_boundary_points(
                    child_truncated_tokens["tokens"],
                    tokenizer=self._tokenizer,
                    boundary=self.boundary,
                    truncate=self.truncation_strategy,
                )

                parent_truncated_tokens = truncate(
                    child_truncated_tokens["tokens"],
                    tokenizer=self._tokenizer,
                    max_tokens=number_allowed,
                    truncation_strategy=self.truncation_strategy,
                    boundary_points=new_boundary_points,
                    ellipsis=self.ellipsis,
                    boundary_name=self.boundary,
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
                inner_text = self._tokenizer.decode(
                    parent_truncated_tokens["tokens"].ids
                )

                display_text = Text()
                display_text.append(left_text, style="bold magenta")
                display_text.append(inner_text, style="bold blue")
                display_text.append(right_text, style="bold magenta")

                panel = Panel(
                    display_text,
                    title=child.name or "",
                    title_align="left",
                    border_style="bold green",
                )
                rich_texts.append(panel)

                tokens_seen += number_allowed

        # sort children back to their original reading order
        sorted_rich_texts = sorted(
            zip(self.children, rich_texts), key=lambda x: x[0].reading_order_idx
        )

        final_rich_texts = [text for (_, text) in sorted_rich_texts]

        return Panel(
            Group(*final_rich_texts),
            title=self.name or "",
            title_align="left",
            border_style="bold blue",
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
        elif isinstance(other, (TextBlock, Block)):
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
        tokenizer: Callable | None = None,
        boundary: Boundary = "token",
        reading_order_idx: int | None = None,
        priority_order_idx: tuple[int, int] | None = None,
    ):
        self._text = text
        self._tokenizer = tokenizer
        self._tokens = None
        self.name = name
        self.max_tokens = max_tokens
        self.truncation_strategy: TruncationStrategy = truncate
        self.max_value = max_value
        self.ellipsis = ellipsis
        self.boundary: Boundary = boundary
        self.reading_order_idx = reading_order_idx
        self.priority_order_idx = priority_order_idx

    def boundary_points(self, boundary, truncation_strategy):
        if boundary is None:
            boundary = self.boundary
        if truncation_strategy is None:
            truncation_strategy = self.truncation_strategy

        return find_boundary_points(
            encoding=self.full_tokens(),
            tokenizer=self._tokenizer,
            boundary=self.boundary,
            truncate=truncation_strategy,
        )

    def set_tokenizer(self, tokenizer):
        self._tokenizer = tokenizer

    def rich_text(
        self,
        max_tokens: int | None = None,
        truncation_strategy: TruncationStrategy | None = None,
        boundary: str | None = None,
        boundary_points: list[int] | None = None,
    ) -> Panel:
        if max_tokens is None:
            max_tokens = self.max_tokens
        if truncation_strategy is None:
            truncation_strategy = self.truncation_strategy

        display_text = Text()

        if truncation_strategy == "never":
            display_text = Text(self.full_text(), style="bold blue")

        else:
            child_truncated_tokens = truncate(
                self.full_tokens(),
                max_tokens=self.max_tokens,
                truncation_strategy=self.truncation_strategy,
                tokenizer=self._tokenizer,
                boundary_name=self.boundary,
                boundary_points=self.boundary_points(
                    self.boundary, self.truncation_strategy
                ),
            )
            parent_truncated_tokens = truncate(
                child_truncated_tokens["tokens"],
                max_tokens=max_tokens,
                truncation_strategy=truncation_strategy,
                tokenizer=self._tokenizer,
                boundary_name=self.boundary,
                boundary_points=boundary_points,
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

    def truncate(
        self,
        max_tokens: int | None = None,
        truncation_strategy: TruncationStrategy | None = None,
        boundary: Boundary | None = None,
    ) -> list[dict[str, Encoding]]:
        if max_tokens is None:
            max_tokens = self.max_tokens
        if truncation_strategy is None:
            truncation_strategy = self.truncation_strategy
        if boundary is None:
            boundary = self.boundary

        if self.truncation_strategy == "never":
            truncated = {
                "remainder_left": Encoding(),
                "remainder_right": Encoding(),
                "tokens": self.full_tokens(),
            }
        else:
            truncated = truncate(
                self.full_tokens(),
                max_tokens=max_tokens,
                truncation_strategy=truncation_strategy,
                ellipsis=self.ellipsis,
                tokenizer=self._tokenizer,
                boundary_name=self.boundary,
                boundary_points=self.boundary_points(
                    boundary=boundary, truncation_strategy=truncation_strategy
                ),
            )
        return [truncated]

    def tokens(
        self,
        max_tokens: int | None = None,
        truncation_strategy: TruncationStrategy | None = None,
        boundary: Boundary | None = None,
    ) -> Encoding:
        return self.truncate(
            max_tokens=max_tokens,
            truncation_strategy=truncation_strategy,
            boundary=boundary,
        )[0]["tokens"]

    def __repr__(self):
        return f'<Block name="{self.name}" size=[{self.full_size()}/{self.max_tokens or "inf"}] text="{self.text()[:25] + "..."}">'
