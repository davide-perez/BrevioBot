from abc import ABC, abstractmethod

class SummarizerBase(ABC):
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt

    @abstractmethod
    def summarize(self, text: str) -> str:
        pass