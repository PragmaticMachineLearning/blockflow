import pytest
from rich import print
from rich.panel import Panel

from blockflow.block import Block, TextBlock
from blockflow.errors import TruncationError
from blockflow.tokenizer import create_tokenizer

tokenizer = create_tokenizer()


def test_create_block_with_text():
    block = Block(text="this is a sample text", max_tokens=1024, tokenizer=tokenizer)
    assert block.full_text() == "this is a sample text"


def test_add_text_to_block():
    block = Block(text="this is", max_tokens=1024, tokenizer=tokenizer)
    block += TextBlock(" a sample text")
    assert block.full_text() == "this is a sample text"


def test_create_children_with_block():
    child_block = Block(text="this is a child block")
    block = Block(children=[child_block], tokenizer=tokenizer)
    assert block.full_text() == "this is a child block"


@pytest.mark.parametrize(
    "text",
    ["sample text", "019845mas..159-una~", "            this is a word             "],
)
def test_block_full_size(text: str):
    block = Block(text=text, tokenizer=tokenizer)
    assert block.full_size() == len(tokenizer.encode(block.full_text()))
    assert block.size() == len(tokenizer.encode(block.text()))


def test_rich_text_method():
    block = Block(text="this is a sample text", tokenizer=tokenizer)
    rich_panel = block.rich_text(max_tokens=10)
    rich_text = block.rich_text()
    print(rich_text)
    assert isinstance(rich_panel, Panel)
    assert isinstance(rich_text, Panel)


def test_seperator():
    block = Block(
        text="this is a sample text",
        separator="\n",
        children=[Block(text="this is another sample text")],
        tokenizer=tokenizer,
    )
    block += "this is an additional text"
    block += TextBlock(text="this is a block text")
    assert (
        block.full_text()
        == "this is a sample text\nthis is another sample text\nthis is an additional text\nthis is a block text"
    )
    with pytest.raises(TypeError):
        block += 1


def test_tokenizer_required():
    block = Block(
        text="this is a sample text",
    )
    with pytest.raises(ValueError):
        block.full_tokens()


def test_representation():
    block = Block(text="this is a sample text", name="Grandparent", tokenizer=tokenizer)
    assert (
        block.__repr__()
        == '<Block name="Grandparent" size=[5/inf] text="this is a sample text...">'
    )


def test_max_tokens():
    with pytest.raises(ValueError):
        Block(text="this is a sample text", max_tokens=-1, tokenizer=tokenizer)


def test_block_length():
    block = Block(text="this is a sample text", tokenizer=tokenizer)
    assert len(block) == len(block.full_text())


def test_append_method():
    block = Block(text="this is a sample text", tokenizer=tokenizer)
    block.append(", append a given text to it")
    assert block.full_text() == "this is a sample text, append a given text to it"


def test_truncate_default():
    context = Block(max_tokens=3, tokenizer=tokenizer)
    context += "This is a sample prompt"
    assert context.text() == "This is a"
    assert context.size() == context.max_tokens


def test_textblock_text():
    text_block = TextBlock(text="this is a sample text", tokenizer=tokenizer)
    assert text_block.full_text() == "this is a sample text"


def test_textblock_tokens_and_representation():
    text_block = TextBlock(text="this is a sample text", tokenizer=tokenizer)
    assert text_block.full_tokens().ids == tokenizer.encode(text_block.text()).ids
    assert (
        text_block.__repr__()
        == '<Block name="None" size=[5/inf] text="this is a sample text...">'
    )


def test_truncate_right():
    context = Block(max_tokens=3, truncate="right", tokenizer=tokenizer)
    context += "This is a sample prompt"
    assert context.text() == "This is a"
    assert context.size() == context.max_tokens


def test_truncate_left():
    context = Block(max_tokens=3, truncate="left", tokenizer=tokenizer)
    context += "This is a sample prompt"
    assert context.text() == " a sample prompt"
    assert context.size() == context.max_tokens


def test_truncate_never():
    context = Block(max_tokens=3, truncate="never", tokenizer=tokenizer)
    context += "This is a sample prompt"

    with pytest.raises(TruncationError):
        context.text()


def test_block_truncate_never():
    context = Block(truncate="never", tokenizer=tokenizer)
    context += "This is a sample prompt"
    assert context.text() == "This is a sample prompt"


def test_block_truncate_never_with_parent():
    child_block_1 = TextBlock(
        text="this is a prompt that should be truncated",
        name="child block 1",
        truncate="right",
        tokenizer=tokenizer,
        max_tokens=20,
    )
    child_block_2 = TextBlock(
        text="this is a sample prompt",
        name="child block 2",
        truncate="never",
        tokenizer=tokenizer,
        # max_tokens=20
    )
    parent = Block(
        name="parent block",
        tokenizer=tokenizer,
        children=[child_block_1, child_block_2],
        max_tokens=5,
    )
    child_texts_before = [child_block.text() for child_block in parent.children]
    assert parent.text() == "this is a sample prompt"
    child_texts_after = [child_block.text() for child_block in parent.children]
    assert child_texts_before == child_texts_after


@pytest.mark.parametrize(
    "text, name, max_tokens, truncate, expected",
    [
        (
            "a b c d e f g h i j k l m n o p",
            "child block",
            10,
            "right",
            "a b c d e f g h i j",
        ),
        ("a b c d e f g h i j", "parent block", 5, "left", " f g h i j"),
        ("a b c d e f g h i j k l m n o p", "child block", 5, "right", "a b c d e"),
        ("a b c d e", "parent block", 1000, "left", "a b c d e"),
    ],
)
def test_child_parent_truncation_heirachy(text, name, truncate, max_tokens, expected):
    child_block = TextBlock(
        text=text,
        name=name,
        truncate=truncate,
        max_tokens=max_tokens,
    )
    parent = Block(
        name=name,
        tokenizer=tokenizer,
        truncate=truncate,
        children=[child_block],
        max_tokens=max_tokens,
    )

    assert parent.text() == expected


def test_truncate_left_ellipsis():
    context = Block(max_tokens=3, truncate="left", ellipsis=True, tokenizer=tokenizer)
    context += "This is a sample prompt"
    assert context.text() == "... sample prompt"
    assert context.size() == context.max_tokens


def test_truncate_right_ellipsis():
    context = Block(max_tokens=3, truncate="right", ellipsis=True, tokenizer=tokenizer)
    context += "This is a sample prompt"
    assert context.text() == "This is..."
    assert context.size() == context.max_tokens


def test_truncate_max_tokens():
    block = Block(
        text="this is a sample text", max_tokens=0, ellipsis=True, tokenizer=tokenizer
    )
    assert block.text() == ""


def test_exceed_max_tokens():
    block = Block(
        text="this is a sample text",
        children=[
            Block(text="this is a second sample text"),
            Block(text="this is a third sample text"),
        ],
        
        tokenizer=tokenizer,
    )
    rich_text = block.rich_text(max_tokens=5)
    final_child = rich_text.renderable.renderables[-1]
    from rich import print

    print(rich_text)
    # import pdb
    
    # pdb.set_trace()
    assert len(rich_text.renderable.renderables) == 3
    assert (
        final_child.renderable.spans[0].style
        == "bold magenta"
    )


def test_block_hierarchy():
    context = Block(max_tokens=9, truncate="left", tokenizer=tokenizer)
    context += "This is a sample prompt"
    context += "\n"
    context += "This is another prompt that's a bit longer"
    # First portion of context gets truncated
    assert context.text() == "This is another prompt that's a bit longer"


def test_newline_boundary_right():
    text_block = TextBlock(
        text="This is the first line.\nThis is the second line that is a little bit longer.",
        max_tokens=10,
        truncate="right",
        tokenizer=tokenizer,
        boundary="line",
    )
    assert text_block.text() == "This is the first line."


def test_newline_boundary_left():
    text_block = TextBlock(
        text="This is the first line.\nThis is the second line that is longer.",
        max_tokens=10,
        truncate="left",
        tokenizer=tokenizer,
        boundary="line",
    )
    assert text_block.text() == "This is the second line that is longer."


def test_whitespace_boundary_right():
    text_block = TextBlock(
        text="Go to https://www.google.com/search?q=how+to+cancel+vscode+testing&oq=how+to+cancel+vscode+testing+&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIGCAEQLhhA0gEIODY5MGowajGoAgCwAgA&sourceid=chrome&ie=UTF-8",
        max_tokens=6,
        truncate="right",
        tokenizer=tokenizer,
        boundary="whitespace",
    )
    assert text_block.text() == "Go to"


def test_whitespace_boundary_left():
    text_block = TextBlock(
        text="Go to https://www.google.com/search?q=how+to+cancel+vscode+testing&oq=how+to+cancel+vscode+testing+&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIGCAEQLhhA0gEIODY5MGowajGoAgCwAgA&sourceid=chrome&ie=UTF-8",
        max_tokens=6,
        truncate="left",
        tokenizer=tokenizer,
        boundary="whitespace",
    )
    assert text_block.text() == ""


@pytest.mark.parametrize(
    "text, max_tokens, truncate, expected",
    [
        # Excess whitespace is because of token boundary
        ("Sentence one. Sentence two.", 3, "left", " Sentence two."),
        (
            "This is the first sentence. Here is another sentence.",
            7,
            "left",
            " Here is another sentence.",
        ),
        ("This is a short sentence. This is a longer sentence.", 4, "left", ""),
        (
            "This is the first sentence. Here is another sentence.",
            7,
            "right",
            "This is the first sentence.",
        ),
        (
            "This is the first sentence. Here is another sentence.",
            3,
            "right",
            "",
        ),
        (
            "This is the first sentence. Here is another sentence.",
            8,
            "right",
            "This is the first sentence.",
        ),
        (
            "This is the first sentence. This is the second sentence. This is the third sentence.",
            12,
            "right",
            "This is the first sentence. This is the second sentence.",
        ),
    ],
)
def test_sentence_boundary(text, max_tokens, truncate, expected):
    text_block = TextBlock(
        text=text,
        max_tokens=max_tokens,
        truncate=truncate,
        tokenizer=tokenizer,
        boundary="sentence",
    )
    assert text_block.text() == expected


@pytest.mark.parametrize(
    "truncate,expected",
    [
        ("right", "This is the first sentence."),
        ("left", " This is the second sentence."),
    ],
)
def test_sentence_boundary_parent(truncate, expected):
    block = Block(
        max_tokens=7,
        truncate="right",
        tokenizer=tokenizer,
        boundary="sentence",
        separator=" ",
    )
    block += "This is the first sentence."
    block += "This is the second sentence."
    assert block.text() == "This is the first sentence. "


def test_newline_boundary_parent():
    child_a = TextBlock(
        text="This is the first line.",
    )
    child_b = TextBlock(
        text="This is the second line that is longer.",
    )
    parent = Block(
        children=[child_a, child_b],
        max_tokens=10,
        truncate="right",
        tokenizer=tokenizer,
        boundary="line",
        separator="\n",
    )
    assert parent.text() == "This is the first line.\n"
