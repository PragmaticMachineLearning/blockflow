import glob

from rich import print

from blockflow.block import Block, TextBlock
from blockflow.tokenizer import create_tokenizer

text_files = glob.glob("data/*.txt")
docs = []
for file in text_files:
    doc = open(file).read()
    docs.append(doc)

# We want an even amount of information from each of the documents
max_tokens = 1024
per_file_max_tokens = 1024 // 3
block = Block(max_tokens=max_tokens, tokenizer=create_tokenizer(), boundary="sentence")
for doc in docs:
    block += TextBlock(
        text=doc,
        max_tokens=per_file_max_tokens,
        boundary="sentence",
    )

print(block.rich_text())
