from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from google import genai

from logger_setup import setup_logger

logger = setup_logger("analyzer")

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


class ThreatAnalyzer:

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY saknas i .env-filen eller miljön."
            )
        # Initiera Gemini-klienten
        self.client = genai.Client(api_key=self.api_key)

    def analyze(self, title: str, text: str) -> Dict[str, Any]:
        prompt = f"""
Du är en erfaren cybersäkerhetsanalytiker. Analysera följande information:

Titel: {title}
Innehåll: {text[:1800]}

Svara EXAKT i följande format (inga markdown-block runt om, enbart raderna):

HOTNIVÅ: [Kritisk / Hög / Medel / Låg]
KATEGORI: [Ransomware / Sårbarhet & CVE / Skadlig kod / Nätfiske & Social Engineering / Övriga hot]
RISKPOÄNG: [heltal 1-10]
SAMMANFATTNING: [max 2 meningar på svenska]
REKOMMENDATION: [konkret åtgärd för IT-avdelningen, 1-2 meningar]
"""

        try:
            # Uppdaterad modell enligt Googles rekommendation
            response = self.client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )
            result_text = response.text.strip()
            return self._parse_response(result_text, text)
        except Exception as e:
            logger.error(f"Gemini-analys misslyckades: {e}")
            return {
                "hotniva": "Fel",
                "kategori": "Övriga hot",
                "risk_score": 5,
                "riskpoang": 5,
                "sammanfattning": f"Kunde inte analysera: {e}",
                "rekommendation": "Kontrollera API-nyckel och nätverksanslutning.",
            }

    def _parse_response(
        self, result_text: str, fallback_text: str
    ) -> Dict[str, Any]:
        hotniva = "Hög"
        kategori = "Övriga hot"
        riskpoang = 5
        sammanfattning = fallback_text[:150]
        rekommendation = "Uppdatera system och övervaka loggar."

        for line in result_text.splitlines():
            line = line.strip()
            if line.startswith("HOTNIVÅ:"):
                hotniva = line.replace("HOTNIVÅ:", "").strip()
            elif line.startswith("KATEGORI:"):
                kategori = line.replace("KATEGORI:", "").strip()
            elif line.startswith("RISKPOÄNG:"):
                try:
                    riskpoang = int(line.replace("RISKPOÄNG:", "").strip())
                except ValueError:
                    pass
            elif line.startswith("SAMMANFATTNING:"):
                sammanfattning = line.replace("SAMMANFATTNING:", "").strip()
            elif line.startswith("REKOMMENDATION:"):
                rekommendation = line.replace("REKOMMENDATION:", "").strip()

        return {
            "hotniva": hotniva,
            "kategori": kategori,
            "risk_score": riskpoang,
            "riskpoang": riskpoang,
            "sammanfattning": sammanfattning,
            "rekommendation": rekommendation,
        }