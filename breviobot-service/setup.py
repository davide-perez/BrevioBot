from setuptools import setup, find_packages

setup(
    name="breviobot-service",
    version="1.0.0",
    packages=find_packages(),    install_requires=[
        "openai>=1.0.0",
        "flask>=3.1.1"
    ]
)
