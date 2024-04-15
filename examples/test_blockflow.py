from blockflow.block import Block, TextBlock
import wikipedia
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from blockflow.tokenizer import create_tokenizer

tokenizer = create_tokenizer("microsoft/phi-2")

torch.set_default_device("cuda")
print("RUNNING THIS FILE")

def search_topic(topic):
    try:
        search_results = wikipedia.search(f"{topic}")

        return [
            wikipedia.page(result, auto_suggest=False).content
            for result in search_results
        ]
    except Exception as e:
        return str(e)


# TODO: use blockflow to handle prompt lengths for each result obtained from the search_topic function, so each result has the same number of tokens in the prompt


def generate_response(prompt: str):
    model = AutoModelForCausalLM.from_pretrained(
        "venkycs/phi-2-instruct", torch_dtype="auto", trust_remote_code=True
    )
    tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2", trust_remote_code=True)

    inputs = tokenizer.encode(prompt, return_tensors="pt", return_attention_mask=False)
    outputs = model.generate(inputs, max_length=1024)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


topic = "USA history"
input = search_topic(topic)
print([len(i) for i in input])
result = []

for text in input:
    truncated_prompt = TextBlock(
        text=text,
        boundary="line",
        tokenizer=tokenizer,
        truncate="right",
        max_tokens=100,
    )
    result.append(truncated_prompt)

    # print(truncated_prompt.full_text())
    # print(truncated_prompt.size())
    # import ipdb

    # ipdb.set_trace()
print([i.size() for i in result])

# prompt = "summarize the follwing content into 3 lines and make it funny: "


# generated_output = generate_response(truncated_prompt.text())
# print(f"RAW INPUTS: {input}")
# print("\n\n")
# print(f"GENERATED OUTPUT: {generated_output}")
