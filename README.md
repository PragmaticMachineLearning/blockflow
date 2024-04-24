

# blockflow
-------
![blockflow](./assets/blockflow.png)


#### Overview

This library offers detailed control over the construction and modification of prompts, tailored to fit within the constraints of a language model's context size. It uses a method akin to HTML and CSS, where CSS controls overflow and sizing on a webpage. Similarly, this library allows users to define and adjust the size and content of different sections within a prompt to ensure optimal use of the available context size.

#### Functionality
* Context and Prompt Segmentation: Breaks down prompts into sections (e.g., Context, Question, Answer Prompt) allowing for selective modification and resizing.
* Adaptive Truncation: Dynamically truncates prompts, prioritizing essential sections, to fit within the limited context window of the language model.
* Visual Simulation: Demonstrates how prompts will appear with different context sizes, providing a visual tool for planning and adjustments.

#### Truncation Examples
* Single Section Truncation: If the context window is too small, the library can truncate less critical sections to preserve the integrity of more important ones (e.g., keeping the Answer Prompt intact).
* Equitable Reduction: When dealing with multiple sections, the library can reduce each section's size equally or opt to entirely drop less critical sections to fit within the context size.

#### Goals
* Ease of Experimentation: Facilitate testing different prompt management strategies to optimize usage of LLM memory.
* Flexible Truncation Control: Users can define specific truncation points (characters, tokens, words, sentences, paragraphs, newlines) and how truncation is visually indicated (e.g., with ellipses).
* Independent Section Management: Allows users to edit, resize, and manage individual sections of a prompt independently, making it easier to adapt prompts to changing context sizes.
* Visualization and Editing Tools: Provides tools to visually simulate and edit prompt layouts to foresee and adjust to how prompts will be truncated or resized.

#### Additional Features
Queue Block and Compression: Incorporate advanced features like queuing blocks of prompts and compressing them using summarization techniques to maximize the effective use of LLM's context.