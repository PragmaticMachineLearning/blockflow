import tiktoken
from transformers import AutoTokenizer

def create_tokenizer(tokenizer_name: str | None = None):

    if tokenizer_name is not None:
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    else:
        tokenizer = tiktoken.encoding_for_model("gpt-4")
    return tokenizer
