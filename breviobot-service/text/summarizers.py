from abc import ABC, abstractmethod
from openai import OpenAI
import subprocess

class SummarizerBase(ABC):
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt

    @abstractmethod
    def summarize(self, text: str) -> str:
        pass


class OllamaSummarizer(SummarizerBase):
    def __init__(self, system_prompt: str, model: str):
        super().__init__(system_prompt)
        self.model = model

    def summarize(self, text: str) -> str:
        full_prompt = f"{self.system_prompt}\n\n{text}"
        result = subprocess.run(
            ["ollama", "run", self.model],
            input=full_prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            raise RuntimeError(f"Error in llama while summarizing: {result.stderr.decode('utf-8')}")
        return result.stdout.decode("utf-8").strip()
    

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
    

class SummarizerFactory:
    @staticmethod
    def create_summarizer(model: str, system_prompt: str, openai_api_key: str) -> SummarizerBase:
        if model.startswith("gpt"):
            if not openai_api_key:
                raise ValueError("OpenAI API key is not set")
            return OpenAISummarizer(system_prompt, model, openai_api_key)
        else:
            return OllamaSummarizer(system_prompt, model)