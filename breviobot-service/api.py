from flask import Flask, request, jsonify
from summarizer import TextSummarizer
from prompts import PROMPTS

app = Flask(__name__)

@app.route("/api/summarize", methods=["POST"])
def summarize():
    data = request.json
    text = data.get("text", "")
    language = data.get("language", "")
    model = data.get("model", "")
    openai_api_key = data.get("openai_api_key", "")
    summarizer = TextSummarizer(openai_api_key, PROMPTS)
    result = summarizer.summarize_text(text, model, language)
    return jsonify({"summary": result})

if __name__ == "__main__":
    app.run(debug=True, port=8000)