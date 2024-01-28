# Step 1: Manual memory management

```python3
prompt = Memory("A long wikipedia article about squirrels...", max_tokens=8192)
compressed_memory = prompt.summarize(max_tokens=4096)
prompt.free_memory() == 4096
prompt += TextBlock("Question: What is the average lifespan of a black squirrel?")

# Maybe there is an analogy for writing to disk, where instead we write to a vector DB?
prompt.save("squirrel_prompt.db") # Vector database

memory = Block(
    Block("Context", max_tokens=4096, name="context"),
    Block("Question", max_tokens=512, name="question"),
    Block("Answer", max_tokens=512, name="answer"),
)
# Maybe this runs a retrieval step on a vector DB and populates the name block?
memory.clear("context")
memory.load(
    source="squirrel_prompt.db",
    query="What is the average lifespan of a black squirrel",
    target="name"
)

# Do we automatically load into available space?  Or do we automatically overwrite the existing content? Maybe this an option?

memory.gc("What is the average lifespan of a black squirrel") # Drops anything unrelated to current question?

context = Block("Context", max_tokens=4096, name="context")
question = Block("Question", max_tokens=512, name="question")
answer = Block("Answer", max_tokens=512, name="answer")

# DSPY like API for running LLM inference
answer = compile("context,question -> answer") # LLM is automatically run here to populate answer
answer = compile("context,history,question -> answer") # LLM is automatically run here to populate answer

# Avoid Redundancy: this might be similar to prompt.summarize(), but before summarizing, we can add a step that
# handles redundancy by removing repeated information in the provided prompt. Question: How do we preserve the prompt's
contextual information after all this processing? -- this should be baked into summarize()

# Chunking: Considering how large datasets are usually broken down to be efficiently processed in RAM, complex prompts can
# also be broken down into chunks before being passed to the language model -- Consider memory paging as an analogy to chunking

# Consider a virtual memory analogy: we can have a virtual memory that has a larger context size compared to the context size of the LLM to be prompted
# for now, we are not sure this will work because thinking about it, the llm might need to be one finetuned for a specific domain. Example is one that 
# was finetuned using COT -- still interesting to dig into this idea!

# Look into how RUST handles memory, it does not use garbage collection. Figure out if it is beneficial in place of garbage collection.

# Look up Reference counting, it is a way to use garbage collection.


# Maybe we can use a context manager to handle memory management?
with LlmagicMemory("A long wikipedia article about squirrels...", max_tokens=8192) as prompt:
    compressed_memory = prompt.summarize(max_tokens=4096)
    assert prompt.free_memory() == 4096
    prompt += TextBlock("Question: What is the average lifespan of a black squirrel?")



```

# Step 2: Automatic memory management

# Garbage collection in python

```python
a = 100
# Snapshot: {'a': 100}
def fn(a):
    b = a * 2
    # Snapshot: {'a': 100, 'b': 200}
    return b

result = fn()
# Snapshot: {'a': 100, 'result': 200}
```

# Garbage collection when prompting LLMs

What's the equivalent?
