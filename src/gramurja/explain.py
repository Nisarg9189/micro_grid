"""Turn the optimiser's advice into a message a farmer can read.

This is the only place a language model appears in the project, and its job is narrow on
purpose: **phrasing and translation, never arithmetic**. Every number is decided by the
optimiser and passed in; the model may only re-word what it is given, into Gujarati or
Hindi if asked.

That boundary is enforced rather than trusted. `verify_numbers` pulls every numeral out of
the generated text and checks each one traces back to the input. If the model invents a
figure -- a saving that was never computed, a time that was never recommended -- the output
is marked unverified and the caller falls back to the deterministic English. A farmer
deciding when to irrigate should never act on a hallucinated litre.

Requires GEMINI_API_KEY, read from the environment or a local .env (which is gitignored).
"""

import json
import os
import pathlib
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field

MODEL = "gemini-flash-latest"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

LANGUAGES = {
    "english": "plain English",
    "gujarati": "Gujarati (ગુજરાતી script)",
    "hindi": "Hindi (देवनागरी script)",
}

_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


@dataclass
class Explanation:
    text: str
    language: str
    verified: bool
    unverified_numbers: list[str] = field(default_factory=list)
    source_lines: list[str] = field(default_factory=list)

    @property
    def safe_text(self) -> str:
        """What is actually safe to show a farmer."""
        return self.text if self.verified else "\n".join(self.source_lines)


def load_env(path: str | pathlib.Path = ".env") -> dict[str, str]:
    """Read a local .env without pulling in a dependency for six lines of parsing."""
    values = {}
    file = pathlib.Path(path)
    if not file.exists():
        return values
    for line in file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def api_key(env_path: str | pathlib.Path = ".env") -> str | None:
    return os.environ.get("GEMINI_API_KEY") or load_env(env_path).get("GEMINI_API_KEY")


def _numbers(text: str) -> set[float]:
    found = set()
    for raw in _NUMBER.findall(text):
        cleaned = raw.replace(",", "")
        try:
            found.add(float(cleaned))
        except ValueError:
            continue
    return found


def verify_numbers(generated: str, source: str) -> list[str]:
    """Return any numeral in the generated text that does not appear in the source.

    Small integers up to 24 are allowed through unchecked: they are hours, counts and
    list markers that legitimately arise from re-wording a recommendation, and treating
    them as fabrications would reject every valid translation.
    """
    allowed = _numbers(source)
    unknown = []
    for raw in _NUMBER.findall(generated):
        try:
            # float() accepts Gujarati and Devanagari digits, which is what a translated
            # message actually contains; anything it cannot parse is treated as suspect.
            value = float(raw.replace(",", ""))
        except ValueError:
            unknown.append(raw)
            continue
        if value in allowed or (value <= 24 and value == int(value)):
            continue
        unknown.append(raw)
    return unknown


def _strip_preamble(text: str) -> str:
    """Drop a leading "Here is the message:" line and markdown emphasis.

    The instruction not to add a preamble is followed most of the time but not always,
    and a farmer-facing message should not open by narrating itself.
    """
    text = text.replace("**", "").replace("*", "").strip()
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) > 1 and lines[0].rstrip().endswith(":") and len(lines[0]) < 90:
        lines = lines[1:]
    return "\n".join(lines).strip()


def _request(prompt: str, key: str, model: str = MODEL, timeout: int = 60) -> str:
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
            # Reasoning tokens count against maxOutputTokens on this model. Left on, a
            # short translation spent 387 of 400 tokens thinking and returned a sentence
            # cut off mid-word. There is nothing here worth reasoning about.
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }).encode()
    request = urllib.request.Request(
        ENDPOINT.format(model=model),
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    candidate = payload["candidates"][0]
    if candidate.get("finishReason") not in (None, "STOP"):
        raise ValueError(f"generation did not finish cleanly: {candidate.get('finishReason')}")
    parts = candidate.get("content", {}).get("parts", [])
    return _strip_preamble("".join(part.get("text", "") for part in parts))


def _prompt(lines: list[str], language: str) -> str:
    described = LANGUAGES.get(language.lower(), LANGUAGES["english"])
    joined = "\n".join(f"- {line}" for line in lines)
    return (
        "You are relaying an irrigation recommendation to a smallholder farmer in "
        "Banaskantha, Gujarat. An optimisation model produced these findings:\n\n"
        f"{joined}\n\n"
        f"Rewrite them as a short message in {described}, at most four sentences, in the "
        "direct plain style a farmer would want.\n\n"
        "Rules you must follow:\n"
        "- Use ONLY the numbers given above. Do not add, round, convert or invent any figure.\n"
        "- Do not promise outcomes that are not stated. Do not add advice of your own.\n"
        "- Keep the reason attached to the instruction, so the farmer can judge it.\n"
        "- Output the message only, with no preamble, heading or bullet markers."
    )


def render_advice(
    briefing: list[str],
    language: str = "gujarati",
    model: str = MODEL,
    env_path: str | pathlib.Path = ".env",
) -> Explanation:
    """Re-word the optimiser's briefing, then check it invented nothing."""
    key = api_key(env_path)
    if not key:
        return Explanation(
            text="\n".join(briefing), language="english", verified=True,
            source_lines=briefing,
        )

    source = "\n".join(briefing)
    try:
        generated = _request(_prompt(briefing, language), key, model=model)
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError) as error:
        return Explanation(
            text="\n".join(briefing), language="english", verified=True,
            unverified_numbers=[f"request failed: {type(error).__name__}"],
            source_lines=briefing,
        )

    unknown = verify_numbers(generated, source)
    return Explanation(
        text=generated,
        language=language,
        verified=not unknown,
        unverified_numbers=unknown,
        source_lines=briefing,
    )
