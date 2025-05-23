from flask import Flask, request, jsonify
from config import Config
from summarizer import TextSummarizer
from prompts import PROMPTS
from translations import UI  # Assuming translations.py is shared or copied into service

app = Flask(__name__)

config = Config.load()

@app.route("/api/summarize", methods=["POST"])
def summarize():
    data = request.json
    text = data.get("text", "")
    language = data.get("language", "")
    summarizer = TextSummarizer(config, PROMPTS, UI)
    result = summarizer.summarize(text)
    return jsonify({"summary": result})

if __name__ == "__main__":
    app.run(debug=True, port=8000)