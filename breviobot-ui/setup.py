from setuptools import setup, find_packages

setup(
    name="breviobot-ui",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.0.0",
        "gtts>=2.3.0",
        "requests>=2.32.3",
        "python-dotenv>=1.0.0",
        "typing-extensions>=4.5.0"
    ],
    python_requires=">=3.9",
    package_data={
        "breviobot_ui": ["py.typed"]
    },
    entry_points={
        "console_scripts": [
            "breviobot-ui=src.app:main",
        ],
    },
)
