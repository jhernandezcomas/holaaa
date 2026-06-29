import json
import re
from pathlib import Path
from typing import Optional

import anthropic


SYSTEM_PROMPT_TEMPLATE = """You are a real-time interview assistant for José Joaquín Hernández Comas.

José is a native Spanish speaker being interviewed in English for maintenance technician positions in the United States. His English is conversational but he is still building technical fluency — so your suggested answers must sound natural and clear, not overly formal or complex.

JOSÉ'S PROFILE:
{profile}

YOUR TASK:
You will receive fragments of what the interviewer says in English. For each message you must:

1. Translate to Spanish what the interviewer said (field "translation") — so José understands immediately
2. Determine if it is a question or a statement (field "is_question")
3. If it IS a question:
   - Write a suggested answer in English that José can say out loud (field "suggested_answer")
     * Use real data from his profile: company names, certifications (EPA 608), tools (AppWork, Yardi), years of experience, etc.
     * Keep it 2–4 sentences — concise and confident, like a real person speaking
     * Use simple, clear English appropriate for someone with conversational fluency
     * Do NOT use overly formal or academic language
   - Translate the suggested answer to Spanish (field "answer_in_spanish") so José knows what he's about to say
4. If it is NOT a question, set suggested_answer and answer_in_spanish to null

IMPORTANT RULES:
- Maintain conversation context across multiple turns — remember what was already discussed
- If a question is about a skill or experience José doesn't have, suggest an honest answer that pivots to a related strength
- Never invent experience that isn't in his profile
- Always respond ONLY with valid JSON, no markdown, no extra text

JSON format:
{{
  "original": "exact original English text",
  "translation": "Spanish translation of what was said",
  "is_question": true,
  "suggested_answer": "suggested English response José can say out loud",
  "answer_in_spanish": "the suggested answer translated to Spanish"
}}"""


class InterviewAssistant:
    def __init__(self, profile_path: str = "profile.md", api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.profile = self._load_profile(profile_path)
        self.history = []

    def _load_profile(self, path: str) -> str:
        p = Path(path)
        if p.exists():
            return p.read_text(encoding="utf-8")
        return "Perfil no disponible. Crea un archivo profile.md con tu información."

    def process(self, text: str) -> Optional[dict]:
        text = text.strip()
        if len(text) < 4:
            return None

        self.history.append({"role": "user", "content": f'El entrevistador dijo: "{text}"'})

        # Keep history to last 30 messages to avoid token overflow
        if len(self.history) > 30:
            self.history = self.history[-30:]

        system = SYSTEM_PROMPT_TEMPLATE.format(profile=self.profile)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system,
                messages=self.history,
            )
            raw = response.content[0].text.strip()
            self.history.append({"role": "assistant", "content": raw})

            return self._parse_json(raw, text)

        except Exception as e:
            print(f"[Claude] Error: {e}")
            return {
                "original": text,
                "translation": "(error al procesar)",
                "is_question": False,
                "suggested_answer": None,
                "answer_in_spanish": None,
            }

    def _parse_json(self, raw: str, fallback_text: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return {
            "original": fallback_text,
            "translation": raw,
            "is_question": False,
            "suggested_answer": None,
            "answer_in_spanish": None,
        }

    def reset(self):
        self.history = []
