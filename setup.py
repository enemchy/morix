import os
from setuptools import find_namespace_packages, setup, find_packages
from typing import Tuple


def read_version() -> Tuple[str, str]:
    version = {}
    with open(os.path.join(os.path.dirname(__file__), 'morix', 'version.py')) as f:
        exec(f.read(), version)
    return version['PROGRAM_NAME'], version['PROGRAM_VERSION']


PROGRAM_NAME, PROGRAM_VERSION = read_version()


setup(
    name=PROGRAM_NAME,
    version=PROGRAM_VERSION,
    packages=find_namespace_packages(exclude=["tests"]),
    package_data={'configs': ['*.yml', '.gptignore','plugins/*', 'promts/*'], 'morix.functions': ['*.yml']},
    include_package_data=True,
    author="Kirill Kusov",
    author_email="dzenkir@gmail.com",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://gitlab.com/good-day-inc/morix/",
    install_requires=[
        'rich', 'prompt_toolkit', 'openai', 'pyyaml', 'colorama', 'tiktoken', 'typer', 'langchain_openai'
    ],
    entry_points={
        'console_scripts': [
            'morix=morix.main:main',
        ],
    },
    python_requires='>=3.10',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
