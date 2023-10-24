from pathlib import Path

from tokenizers import Tokenizer

GPT4_TOKENIZER_JSON = Path(__file__).parent / "gpt4_tokenizer.json"


def create_tokenizer(tokenizer_name: str | None = None):
    if tokenizer_name is not None:
        tokenizer = Tokenizer.from_pretrained(tokenizer_name)
    else:
        tokenizer = Tokenizer.from_file(str(GPT4_TOKENIZER_JSON.resolve()))
    return tokenizer
