prompt_text = build_prompt(purpose, top_20_systems)
from google.colab import drive
drive.mount('/content/drive')
from openai import OpenAI
client = OpenAI(api_key="[API KEY]")
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You analyze source code for OS support."},
        {"role": "user", "content": prompt_text}
    ]
)
llm_answer = response.choices[0].message.content
print(llm_answer)
