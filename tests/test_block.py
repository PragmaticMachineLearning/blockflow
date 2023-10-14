from llmagic.block import Block, TextBlock
from llmagic.tokenizer import tokenizer
from rich.panel import Panel


def test_create_block_with_text():
    block = Block(text= "this is a sample text", max_tokens=1024)
    assert block.full_text() == "this is a sample text"

def test_add_text_to_block():
    block = Block(text="this is", max_tokens=1024)
    block += TextBlock(" a sample text")
    assert block.full_text() == "this is a sample text"

def test_create_children_with_block():
    child_block = Block(text="this is a child block")
    block = Block(children=[child_block])
    assert block.full_text() == "this is a child block"

def test_block_full_size():
    block = Block(text="this is a sample text")
    assert block.full_size() == len(tokenizer.encode(block.full_text()))
    assert block.size() == len(tokenizer.encode(block.full_text()))

def test_rich_text_method():
    block = Block(text="this is a sample text")
    rich_panel = block.rich_text(max_tokens=10)
    assert isinstance(rich_panel, Panel)        

def test_append_method():
    block = Block(text= 'this is a sample text')
    block.append(", append a given text to it")
    assert block.full_text() == 'this is a sample text, and i am going to append a given text to it'




def test_block():
    context = Block(max_tokens=1024)
    context += "This is a sample prompt"
    assert context.text() == "This is a sample prompt"


def test_truncate_default():
    context = Block(max_tokens=3)
    context += "This is a sample prompt"
    assert context.text() == "This is a"
    assert context.size() == 3


def test_truncate_right():
    context = Block(max_tokens=3, truncate="right")
    context += "This is a sample prompt"
    assert context.text() == "This is a"
    assert context.size() == 3


def test_truncate_left():
    context = Block(max_tokens=3, truncate="left")
    context += "This is a sample prompt"
    assert context.text() == " a sample prompt"
    assert context.size() == 3


def test_truncate_left_ellipsis():
    context = Block(max_tokens=3, truncate="left", ellipsis=True)
    context += "This is a sample prompt"
    assert context.text() == "... sample prompt"
    assert context.size() == 3


def test_truncate_right_ellipsis():
    context = Block(max_tokens=3, truncate="right", ellipsis=True)
    context += "This is a sample prompt"
    assert context.text() == "This is..."
    assert context.size() == 3


def test_block_hierarchy():
    context = Block(max_tokens=9, truncate="left")
    context += "This is a sample prompt"
    context += "\n"
    context += "This is another prompt that's a bit longer"
    # First portion of context gets truncated
    assert context.text() == "This is another prompt that's a bit longer"

