from setuptools import setup, find_packages

setup(
    name="breviobot-ui",
    version="1.0.0",
    packages=find_packages(),    install_requires=[
        "streamlit>=1.0.0",
        "gtts>=2.3.0",
        "requests>=2.32.3"
    ]
)
