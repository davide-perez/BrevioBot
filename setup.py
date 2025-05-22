from setuptools import setup, find_packages

setup(
    name="breviobot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit",
        "openai",
        "python-dotenv",
        "gtts",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A bot that summarizes text using AI models",
    keywords="summarization, AI, streamlit",
    python_requires=">=3.8",
)
