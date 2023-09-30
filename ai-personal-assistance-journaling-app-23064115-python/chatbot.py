import openai

# Replace 'YOUR_OPENAI_API_KEY' with your actual API key
openai.api_key = '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'

# Replace 'conversation' with the actual conversation text you want to summarize
conversation = """
Person 1: Hello!
Person 2: Hi there, how can I assist you today?
Person 1: I have a question about Python programming.
Person 2: Sure, go ahead and ask your question.
Person 1: ...
"""

# Make the API call to generate the summary
response = openai.Completion.create(
    engine="text-davinci-002",  # GPT-3.5 (ChatGPT) engine
    prompt=conversation,
    max_tokens=100,  # Adjust the length of the summary as needed
)

# Extract the generated summary from the response
summary = response['choices'][0]['text']
print("summary--",summary)







import os

import openai

PROMPT = summary

openai.api_key = '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'

response = openai.Image.create(
    prompt=PROMPT,
    n=1,
    size="256x256",
)

print(response["data"][0]["url"])