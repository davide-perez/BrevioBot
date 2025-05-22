import subprocess
import os
from openai import OpenAI
from dotenv import load_dotenv
from prompts import PROMPTS
from translations import UI

load_dotenv()

def summarize_file(path, model, lang):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return summarize_text(text, model, lang)

def summarize_text(text, model, lang):
    if lang not in PROMPTS:
        raise ValueError(f"Prompt non disponibile per la lingua: {lang}")
    if lang not in UI:
        raise ValueError(f"Traduzioni non disponibili per la lingua: {lang}")

    system_prompt = PROMPTS[lang]
    user_prompt = text

    if model.startswith("gpt"):
        return summarize_with_openai(system_prompt, user_prompt, model, lang)
    else:
        full_prompt = system_prompt + "\n\n" + text
        return summarize_with_ollama(full_prompt, model, lang)

def summarize_with_openai(system_prompt, user_prompt, model, lang):
    T = UI[lang]
    api_key = os.environ.get("BREVIOBOT_OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(T["missing_api_key"])
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def summarize_with_ollama(prompt, model, lang):
    T = UI[lang]
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        raise RuntimeError(f"{T['ollama_error_prefix']} {result.stderr.decode('utf-8')}")
    return result.stdout.decode("utf-8").strip()


