from llmagic.block import Block, TextBlock
from llmagic.tokenizer import tokenizer
from rich.panel import Panel
import pytest


def test_create_block_with_text():
    block = Block(text="this is a sample text", max_tokens=1024)
    assert block.full_text() == "this is a sample text"


def test_add_text_to_block():
    block = Block(text="this is", max_tokens=1024)
    block += TextBlock(" a sample text")
    assert block.full_text() == "this is a sample text"


def test_create_children_with_block():
    child_block = Block(text="this is a child block")
    block = Block(children=[child_block])
    assert block.full_text() == "this is a child block"


@pytest.mark.parametrize("text", ["sample text", "019845mas..159-una~", "            this is a word             "])
def test_block_full_size(text: str):
    block = Block(text=text)
    assert block.full_size() == len(tokenizer.encode(block.full_text()))
    assert block.size() == len(tokenizer.encode(block.text()))


def test_rich_text_method():
    block = Block(text="this is a sample text")
    rich_panel = block.rich_text(max_tokens=10)
    rich_text = block.rich_text()
    assert isinstance(rich_panel, Panel)
    assert isinstance(rich_text, Panel)


def test_seperator():
    block = Block(text="this is a sample text", separator='\n',
                  children=[Block(text='this is another sample text')])
    block += "this is an additional text"
    block += TextBlock(text="this is a block text")
    assert block.full_text() == "this is a sample text\nthis is another sample text\nthis is an additional text\nthis is a block text"
    with pytest.raises(TypeError):
        block += 1

def test_representation():

    block = Block(text="this is a sample text", name="Grandparent")
    assert block.__repr__(
    ) == '<Block name="Grandparent" size=[5/inf] text="this is a sample text...">'

def test_max_tokens():
    with pytest.raises(ValueError):
        Block(text="this is a sample text", max_tokens=-1)


def test_block_length():
    block = Block(text="this is a sample text")
    assert len(block) == len(block.full_text())


def test_append_method():
    block = Block(text='this is a sample text')
    block.append(", append a given text to it")
    assert block.full_text() == 'this is a sample text, append a given text to it'


def test_truncate_default():
    context = Block(max_tokens=3)
    context += "This is a sample prompt"
    assert context.text() == "This is a"
    assert context.size() == context.max_tokens


def test_textblock_text():
    text_block = TextBlock(text="this is a sample text")
    assert text_block.full_text() == "this is a sample text"


def test_textblock_tokens_and_representation():
    text_block = TextBlock(text="this is a sample text")
    assert text_block.full_tokens() == tokenizer.encode(text_block.text())
    assert text_block.__repr__(
    ) == '<Block name="None" size=[5/inf] text="this is a sample text...">'


def test_truncate_right():
    context = Block(max_tokens=3, truncate="right")
    context += "This is a sample prompt"
    assert context.text() == "This is a"
    assert context.size() == context.max_tokens


def test_truncate_left():
    context = Block(max_tokens=3, truncate="left")
    context += "This is a sample prompt"
    assert context.text() == " a sample prompt"
    assert context.size() == context.max_tokens


def test_truncate_left_ellipsis():
    context = Block(max_tokens=3, truncate="left", ellipsis=True)
    context += "This is a sample prompt"
    assert context.text() == "... sample prompt"
    assert context.size() == context.max_tokens

def test_truncate_right_ellipsis():
    context = Block(max_tokens=3, truncate="right", ellipsis=True)
    context += "This is a sample prompt"
    assert context.text() == "This is..."
    assert context.size() == context.max_tokens

def test_truncate_max_tokens():
    block = Block(text="this is a sample text", max_tokens=1, ellipsis=True)
    assert block.text() == "this"

def test_exceed_max_tokens():
    block = Block(text="this is a sample text", children=[Block(
        text='this is a second sample text'), Block(text="this is a third sample text")])
    rich_text = block.rich_text(max_tokens=10)
    final_child = rich_text.renderable.renderables[-1]
    assert len(rich_text.renderable.renderables) == 3
    assert final_child.renderable.renderables[0].renderable.spans[0].style == "bold magenta"


def test_block_hierarchy():
    context = Block(max_tokens=9, truncate="left")
    context += "This is a sample prompt"
    context += "\n"
    context += "This is another prompt that's a bit longer"
    # First portion of context gets truncated
    assert context.text() == "This is another prompt that's a bit longer"
