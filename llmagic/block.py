from llmagic.tokenizer import tokenizer
from typing import NoReturn
import typing
from rich.panel import Panel
from rich.console import Group
from rich.style import Style
from rich.text import Text
import hashlib


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

    
        if self.max_tokens is None:
            pass
        elif self.max_tokens < 0:
            raise ValueError(f"max_tokens should be a positive integer and not {self.max_tokens}")
    
        

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
        
        return self._truncate(joined_tokens)['tokens']
    
    @property
    def full_size(self):
        return len(self.full_tokens)

    @property
    def size(self):
        return len(self.tokens)
        

    @property
    def rich_text(self) -> Panel:

        # name_hash = hashlib.md5(self.name.encode()).digest()[:3]    
        # colors = ["bold blue", "red", "purple"]  
        # color_index = int.from_bytes(name_hash, 'big') % len(colors)
        # color = colors[color_index]
        
        # name_to_color = {
        #     name: f"#{hash(name) & 0xFFFFFF:06x}"  # Generate a unique color based on the name's hash
        #     for name in [self.name]
        # }

        # # Determine the style based on the 'name' attribute
        # style = Style(color=name_to_color.get(self.name))


        remainder_left, remainder_right, tokens = self._truncate(self.full_tokens)
        
        display_text = Text()
        offset = 0
        while offset < len(remainder_left):
            # inspect length of child
            for child in self.children:
                if len(child) < len(remainder_left): # color in magenta
                    display_text.append(child, style="bold magenta")
                # elif len(child) < len()
                # There is one tricky case where the child gets split in two that we'll have to handle
                # and we also have to turn off the child coloring
            offset +=1 

        return Panel(

            Group(*(child.rich_text for child in self.children)),
            title=self.name or "",
            title_align="left",
            # border_style="bold blue",
            border_style=f"bold blue",
        )
        
    

    @property
    def text(self) -> str:
        return tokenizer.decode(self.tokens)
    


    def __repr__(self):
        return f'<TextBlock size=[{self.full_size}/{self.max_tokens or "inf"}] text="{self.text[:25] + "..."}">'

    def _truncate(self, tokens: list[int]) -> dict[str, list[int]]:
        size = len(tokens)
        remainder_right = []
        remainder_left = []
        if self.max_tokens is not None and size > self.max_tokens:
            match self.truncatation_strategy:
                case "right":
                    remainder_right = tokens[self.max_tokens:]
                    tokens = tokens[: self.max_tokens]
                case "left":
                    remainder_left = tokens[:-self.max_tokens]
                    tokens = tokens[-self.max_tokens :]
                case _:
                    # No truncation
                    pass
        return {'remainder_left': remainder_left,
                'remainder_right': remainder_right, 
                'tokens': tokens}

    def __add__(self, other):
        if isinstance(other, str):
            self.children.append(TextBlock(text=other))
            return self
        elif isinstance(other, Block):
            self.children.append(other)
            return self
        else:
            raise TypeError("Block can only be added to a string")
    
    
    def __len__(self):
        return len(self.full_text)
    


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
        truncate_tokens = self._truncate(self.full_tokens)
        right_text = tokenizer.decode(truncate_tokens['remainder_right'])
        left_text = tokenizer.decode(truncate_tokens['remainder_left'])
        inner_text = tokenizer.decode(truncate_tokens['tokens'])

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
        truncated = self._truncate(self.full_tokens)
        return truncated['tokens']
