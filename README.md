

# blockflow
-------
<!-- ![blockflow](./assets/blockflow.png) -->

<img src="./assets/blockflow.png" alt="blockflow" width="600" height="400">


Blockflow is a system designed to manage and structure prompts for large language models. The system's primary goal is to handle text inputs efficiently, ensuring they fit within token limits while maintaining logical content boundaries. This is crucial when working with large models where prompt length constraints are a significant factor.

### Key Features

**Truncation Strategies**: Blockflow provides several truncation strategies to manage how text is shortened when it exceeds token limits. These strategies ensure that prompts are trimmed in a way that retains the most important content.

- **Right Truncation**: Removes tokens from the end of the text until the token limit is met, ideal for keeping the initial context intact.

- **Left Truncation**: Removes tokens from the beginning, useful when the end of the text contains the most critical information.

- **Never Truncate**: Ensures that the text is not truncated, raising an error if the text exceeds the token limit. This is important when it is critical to retain all the content.

**Boundary Conditions**: Blockflow supports various boundary conditions that guide where truncation should occur. These boundaries ensure that truncation happens at logical points within the text, preserving the meaning and structure.

- **Token Boundary**: Truncation can occur at any token, offering maximum flexibility.

- **Line Boundary**: Ensures truncation happens at line breaks, useful for structured text or code.

- **Whitespace Boundary**: Truncation occurs at whitespace, preventing the splitting of words, which helps maintain readability.

- **Sentence Boundary**: Truncation happens at sentence boundaries, ensuring that sentences are not cut off mid-way, which is crucial for maintaining textual coherence.

### Hierarchical Structure: Parent and Child Blocks
Blockflow's architecture is designed around a hierarchical structure where blocks can contain other blocks, known as child blocks. This parent-child relationship allows for the creation of complex, nested prompt structures that can be managed and truncated as a single entity or at multiple levels.

- **Parent Blocks**: A parent block can encapsulate multiple child blocks, each with its own text content, token limits, and truncation strategies. The parent block oversees the overall structure, applying truncation based on its own parameters and those of its children.

- **Child Blocks**: Child blocks inherit certain characteristics from their parent block but can also have their own distinct properties, such as specific truncation strategies or boundaries. This allows for granular control over each part of the prompt, ensuring that important content is preserved according to its priority within the hierarchy.

- **Truncation Hierarchy**: When a parent block is truncated, the truncation process cascades down to its children. However, child blocks with a "never" truncation strategy are protected, ensuring that crucial parts of the text are not lost. The system carefully balances the token limits of parent and child blocks to maintain the integrity of the prompt.


### Example usage

```python
from blockflow.block import Block, TextBlock
from blockflow.tokenizer import create_tokenizer
from rich import print

# Create a tokenizer
tokenizer = create_tokenizer()

# Define child blocks with individual texts
child_block_1 = TextBlock(
    text="This is the first child block.",
    tokenizer=tokenizer,
    max_tokens=4,
    truncate="right",
    name="child_block_1",
)

child_block_2 = TextBlock(
    text="This is the second child block, containing more detailed information.",
    tokenizer=tokenizer,
    max_tokens=20,
    truncate="right",
    name="child_block_2",
)

# Define a parent block that contains the child blocks
parent_block = Block(
    name="Parent Block",
    max_tokens=10,
    truncate="right",
    separator=" | ",
    tokenizer=tokenizer,
    children=[child_block_1, child_block_2],
)

# Get the truncated text for the parent block, which includes its children
truncated_text = parent_block.rich_text()
print(truncated_text)

```

### Installation
You can install Blockflow directly from PyPI using pip:

```bash
pip install blockflow
```

### Contributing
Contributions to Blockflow are welcome! Please fork the repository, make your changes, and submit a pull request.

### License
Blockflow is licensed under the apache License. See the LICENSE file for more details.

### Contact
For questions or feedback, feel free to open an issue on GitHub or contact the project maintainers directly.

