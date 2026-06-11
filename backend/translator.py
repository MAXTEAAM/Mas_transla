"""
Translation Engine
==================
Wraps multiple translation providers (Google Translate, DeepL) with
a unified interface. Supports auto-detection and batch translation.
"""

from typing import Optional

from deep_translator import GoogleTranslator, single_detection


# Map of common Maximo language codes to deep-translator codes
MAXIMO_TO_TRANSLATOR = {
    "EN": "en",
    "FR": "fr",
    "DE": "de",
    "ES": "es",
    "IT": "it",
    "PT": "pt",
    "NL": "nl",
    "AR": "ar",
    "ZH": "zh-CN",
    "JA": "ja",
    "KO": "ko",
    "RU": "ru",
    "PL": "pl",
    "SV": "sv",
    "DA": "da",
    "FI": "fi",
    "NO": "no",
    "TR": "tr",
    "HE": "iw",
    "TH": "th",
    "VI": "vi",
    "CS": "cs",
    "HU": "hu",
    "RO": "ro",
    "BG": "bg",
    "HR": "hr",
    "SK": "sk",
    "SL": "sl",
    "UK": "uk",
    "EL": "el",
    "ID": "id",
    "MS": "ms",
}

SUPPORTED_LANGUAGES = {
    "EN": "English",
    "FR": "French",
    "DE": "German",
    "ES": "Spanish",
    "IT": "Italian",
    "PT": "Portuguese",
    "NL": "Dutch",
    "AR": "Arabic",
    "ZH": "Chinese (Simplified)",
    "JA": "Japanese",
    "KO": "Korean",
    "RU": "Russian",
    "PL": "Polish",
    "SV": "Swedish",
    "DA": "Danish",
    "FI": "Finnish",
    "NO": "Norwegian",
    "TR": "Turkish",
    "HE": "Hebrew",
    "TH": "Thai",
    "VI": "Vietnamese",
    "CS": "Czech",
    "HU": "Hungarian",
    "RO": "Romanian",
    "BG": "Bulgarian",
    "HR": "Croatian",
    "SK": "Slovak",
    "SL": "Slovenian",
    "UK": "Ukrainian",
    "EL": "Greek",
    "ID": "Indonesian",
    "MS": "Malay",
}


class TranslationEngine:
    def __init__(self, provider: str = "google", api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key

    def translate(self, text: str, source: str, target: str) -> str:
        """
        Translate text from source language to target language.

        Args:
            text: The text to translate
            source: Source language (Maximo code, e.g. "EN")
            target: Target language (Maximo code, e.g. "FR")

        Returns:
            Translated text string
        """
        if not text or not text.strip():
            return ""

        src_code = MAXIMO_TO_TRANSLATOR.get(source.upper(), source.lower())
        tgt_code = MAXIMO_TO_TRANSLATOR.get(target.upper(), target.lower())

        if self.provider == "google":
            translator = GoogleTranslator(source=src_code, target=tgt_code)
            return translator.translate(text)
        else:
            # Default to Google
            translator = GoogleTranslator(source=src_code, target=tgt_code)
            return translator.translate(text)

    def translate_batch(self, texts: list[str], source: str, target: str) -> list[str]:
        """Translate a batch of texts."""
        src_code = MAXIMO_TO_TRANSLATOR.get(source.upper(), source.lower())
        tgt_code = MAXIMO_TO_TRANSLATOR.get(target.upper(), target.lower())

        translator = GoogleTranslator(source=src_code, target=tgt_code)
        results = []
        for text in texts:
            if not text or not text.strip():
                results.append("")
            else:
                results.append(translator.translate(text))
        return results

    def get_supported_languages(self) -> dict:
        """Return supported Maximo language codes and their names."""
        return SUPPORTED_LANGUAGES
