from summarizer.base import SummarizerBase
from openai import OpenAI

class OpenAISummarizer(SummarizerBase):
    def __init__(self, system_prompt: str, model: str, api_key: str):
        super().__init__(system_prompt)
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def summarize(self, text: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()