"""
Red team: loads and optionally mutates injection payloads.
"""

import random
from pathlib import Path

PAYLOAD_DIR = Path(__file__).parent / "payloads"


def load_payload(name: str) -> str:
    path = PAYLOAD_DIR / f"{name}.txt"
    return path.read_text()


def load_all_payloads() -> dict[str, str]:
    payloads = {}
    for path in sorted(PAYLOAD_DIR.glob("*.txt")):
        payloads[path.stem] = path.read_text()
    return payloads


def mutate_payload(payload: str, delimiter_start: str = "", delimiter_end: str = "") -> str:
    """For delimiter_mimic payload, substitute actual delimiter values."""
    result = payload
    if delimiter_end:
        result = result.replace("{delimiter_end}", delimiter_end)
    if delimiter_start:
        result = result.replace("{delimiter_start}", delimiter_start)
    return result


def pad_payload(payload: str, target_words: int) -> str:
    """Pad a payload with filler text to reach a target document length."""
    current_words = len(payload.split())
    if current_words >= target_words:
        return payload

    filler_sentences = [
        "The system performed within expected parameters during the evaluation period.",
        "Additional data points were collected from secondary monitoring stations.",
        "Baseline measurements confirmed consistency with prior observations.",
        "The research team noted several areas for further investigation.",
        "Preliminary findings suggest alignment with the proposed hypothesis.",
        "Cross-referencing with external datasets validated the initial conclusions.",
        "Operational metrics remained stable throughout the observation window.",
        "The methodology followed established protocols for reproducibility.",
        "Supplementary analysis revealed no significant deviations from the norm.",
        "Documentation was updated to reflect the latest configuration changes.",
    ]

    lines = payload.split("\n")
    # Insert filler at the beginning
    filler_lines = []
    while len(" ".join(filler_lines).split()) + current_words < target_words:
        filler_lines.append(random.choice(filler_sentences))
    # Prepend filler before the payload content
    return "\n".join(filler_lines[:3]) + "\n\n" + payload + "\n\n" + "\n".join(filler_lines[3:])
