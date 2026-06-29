import json
import re
from pathlib import Path

import anthropic


SYSTEM_PROMPT_TEMPLATE = """Eres un asistente de entrevistas de trabajo en tiempo real.

La persona que usas este asistente habla español como idioma nativo y está siendo entrevistada en inglés.

PERFIL DEL CANDIDATO:
{profile}

TU TAREA:
Recibirás fragmentos de lo que dice el entrevistador en inglés. Para cada mensaje debes:

1. Traducir al español lo que dijo el entrevistador (campo "translation")
2. Determinar si es una pregunta o afirmación (campo "is_question")
3. Si es una pregunta:
   - Proporciona una respuesta sugerida en inglés basada en el perfil del candidato (campo "suggested_answer")
   - Traduce esa respuesta al español para que el candidato entienda qué va a decir (campo "answer_in_spanish")
4. Si no es una pregunta, pon null en los campos de respuesta

REGLAS IMPORTANTES:
- Las respuestas sugeridas deben sonar naturales y profesionales, como si el candidato hablara espontáneamente
- Usa datos específicos del perfil cuando sea relevante (números, tecnologías, empresas reales)
- Sé conciso: respuestas de 2-4 oraciones son ideales para una entrevista
- Si el perfil no tiene información suficiente para responder una pregunta específica, da una respuesta genérica pero sólida
- Mantén el contexto de la conversación previa

Responde ÚNICAMENTE con JSON válido, sin markdown, sin texto adicional:
{{
  "original": "texto original en inglés",
  "translation": "traducción al español",
  "is_question": true,
  "suggested_answer": "respuesta sugerida en inglés",
  "answer_in_spanish": "la respuesta sugerida traducida al español"
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

    def process(self, text: str) -> dict | None:
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
