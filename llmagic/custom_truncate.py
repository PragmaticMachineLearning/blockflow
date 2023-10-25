from tokenizers import Encoding
from tokenizer import create_tokenizer
import copy

ORIGINAL_TRUNCATE = Encoding.truncate


def truncate_(self, *args, **kwargs):
    copied = copy.deepcopy(self)
    ORIGINAL_TRUNCATE(copied, *args, **kwargs)
    return copied


Encoding.truncate = truncate_

tokens = create_tokenizer().encode("this is a sample text")
truncated_tokens = tokens.truncate(max_length=2)
print(f'truncated tokens {truncated_tokens}')
print(f'original tokens {tokens}')
