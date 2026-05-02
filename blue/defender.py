"""
Blue team: builds defended prompts with delimiter-wrapped documents.
"""

import os
from pathlib import Path

TEMPLATE_DIR = Path(__file__).parent / "templates"


def load_template(name: str) -> str:
    path = TEMPLATE_DIR / f"{name}.txt"
    return path.read_text()


def build_prompt(
    task: str,
    document: str,
    delimiter_start: str,
    delimiter_end: str,
    template_name: str = "basic",
) -> str:
    """Build a complete prompt with delimiter-wrapped document content."""
    template = load_template(template_name)
    return template.format(
        task=task,
        document=document,
        delimiter_start=delimiter_start,
        delimiter_end=delimiter_end,
    )


def build_prompt_no_delimiter(task: str, document: str) -> str:
    """Build a baseline prompt WITHOUT delimiters (for comparison)."""
    return f"{task}\n\nHere is the document:\n\n{document}\n\nProvide your response."


def build_two_pass_prompts(document, delimiter_start, delimiter_end):
    """Return (extract_prompt, summarize_template) for two-pass defense."""
    extract_tpl = load_template("two_pass_extract")
    extract_prompt = extract_tpl.format(
        document=document,
        delimiter_start=delimiter_start,
        delimiter_end=delimiter_end,
    )
    summarize_tpl = load_template("two_pass_summarize")
    return extract_prompt, summarize_tpl
