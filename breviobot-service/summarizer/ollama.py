from summarizer.base import SummarizerBase
import subprocess

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