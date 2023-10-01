from llmagic.block import Block


def test_block():
    context = Block(max_tokens=1024)
    context += "This is a sample prompt"
    assert context.text == "This is a sample prompt"


def test_truncate_default():
    context = Block(max_tokens=3)
    context += "This is a sample prompt"
    assert context.text == "This is a"
    assert context.size == 3


def test_truncate_right():
    context = Block(max_tokens=3, truncate="right")
    context += "This is a sample prompt"
    assert context.text == "This is a"
    assert context.size == 3


def test_truncate_left():
    context = Block(max_tokens=3, truncate="left")
    context += "This is a sample prompt"
    assert context.text == " a sample prompt"
    assert context.size == 3


def test_block_hierarchy():
    context = Block(max_tokens=9, truncate="left")
    context += "This is a sample prompt"
    context += "\n"
    context += "This is another prompt that's a bit longer"
    # First portion of context gets truncated
    assert context.text == "This is another prompt that's a bit longer"
