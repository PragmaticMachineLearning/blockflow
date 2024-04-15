blockflow
-------

### What problem does this solve?
It can be hard to manage prompts and control what happens when you have too many tokens for your context size.
This library is designed to help you have more fine grained control over how your prompts change / adapt to different context sizes.

It works similar to how HTML / CSS work together to layout a webpage.  CSS styles control what happens when content overflows
and control how large elements are within the page.  Similarly we might want to control how large each named section of a prompt is
within the LLM context.

Let's say you have 3 sections to your prompt.

[  Context     ][ Question     ][ Answer Prompt]

If you only have a small context window to work with, your prompt will be truncated. The vertical line indicates where truncation happens.

[ LLM Context Size                  ]
[  Context      ][ Question     ][ Answer| Prompt ]

But in reality you might want to control what content is lost when you need to truncate, e.g. to make sure the answer prompt stays
untouched by truncating the right hand side of the context.

[ LLM Context Size                  ]
[  Context|     ][ Question     ][ Answer Prompt ]

As another example: if you have 10 sections of context, you might want to choose between decreasing each sections size equally or
opting to drop a section all together.  With blockflow it's easy to experiment with different strategies to make sure
you get the behavior you want.

### Goals:
- Make it easy to experiment with how you manage LLM memory
- Queue Block
- Compression via LLM summarization
- Make it easy to control how your prompt is truncated
- Make it easy to visualize your prompts
- Make it easy to edit individual sections of your prompt indepedently
- Make it easy to control where valid truncation points are (chars, tokens, words, sentences, paragraphs, newlines, etc.)
- Truncation that appends ellipses to indicate content was truncated
