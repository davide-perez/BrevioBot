from setuptools import setup, find_packages

setup(
    name="breviobot-service",
    version="1.0.0",
    packages=find_packages(),    install_requires=[
        "openai>=1.0.0",
        "flask>=3.1.1",
        "flask-limiter>=3.5.0",
        "flask-cors>=4.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "faster-whisper>=0.9.0"
    ]
)
