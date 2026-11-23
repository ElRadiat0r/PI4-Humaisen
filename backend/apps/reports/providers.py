"""Fournisseurs de brouillons. Le mode démo n'appelle aucun service externe."""
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class AIProviderError(Exception):
    pass


class DemoProvider:
    name = "synthetic-demo"
    model_name = "template-v1"

    def generate(self, project_data):
        description = project_data["description"].strip()
        return {
            "overview": f"Projet « {project_data['title']} » — domaine : {project_data['domain']}.",
            "findings": [f"Éléments déclarés par le client : {description}", "Ces éléments n'ont pas été vérifiés par une recherche documentaire."],
            "plan": ["Confirmer objectifs, contraintes et échéances avec le client.", "Examiner les documents et devis disponibles avec l'expert.", "Présenter options, coûts et risques avant décision."],
            "estimate": "Aucun devis ni montant n'a été fourni dans les données du dossier.",
            "assumptions": ["Aucune hypothèse métier n'est validée dans ce brouillon."],
            "risks": ["Compléter l'analyse avec les pièces justificatives et l'expertise humaine."],
            "sources": ["Description du dossier fournie par le client."],
            "review_notice": "Brouillon de démonstration synthétique : à compléter et valider par un HumAI.",
        }


def _anonymize(text):
    """Masque les e-mails et numéros de téléphone simples avant envoi externe."""
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
    return re.sub(r"(?<!\w)(?:\+?\d[\d .()/-]{7,}\d)(?!\w)", "[TELEPHONE]", text)


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, endpoint, api_key, model):
        self.endpoint, self.api_key, self.model_name = endpoint, api_key, model

    def generate(self, project_data):
        safe_data = {**project_data, "title": _anonymize(project_data["title"]), "description": _anonymize(project_data["description"])}
        payload = {
            "model": self.model_name, "temperature": 0.2, "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "Rédige un brouillon de restitution en français. N'invente aucun fait ni montant. Retourne un objet JSON avec overview (texte), findings (liste), plan (liste), estimate (texte), assumptions (liste), risks (liste), sources (liste) et review_notice (texte). Signale les informations manquantes et rappelle la validation humaine."},
                {"role": "user", "content": json.dumps(safe_data, ensure_ascii=False)},
            ],
        }
        request = Request(self.endpoint, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}, method="POST")
        try:
            with urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
            content = json.loads(result["choices"][0]["message"]["content"])
        except (HTTPError, URLError, TimeoutError, KeyError, IndexError, ValueError) as exc:
            raise AIProviderError("Le fournisseur IA n'a pas pu produire le brouillon.") from exc
        if not isinstance(content, dict):
            raise AIProviderError("La réponse IA doit être un objet JSON.")
        return content


def get_provider():
    provider_name = os.getenv("AI_PROVIDER", getattr(settings, "AI_PROVIDER", "demo")).lower()
    if provider_name == "demo":
        return DemoProvider()
    if provider_name == "openai":
        endpoint, api_key, model = (
            os.getenv(env_name, getattr(settings, setting_name, ""))
            for env_name, setting_name in (("AI_API_URL", "AI_API_URL"), ("AI_API_KEY", "AI_API_KEY"), ("AI_MODEL", "AI_MODEL"))
        )
        if not endpoint or not api_key or not model:
            raise AIProviderError("AI_API_URL, AI_API_KEY et AI_MODEL sont requis.")
        return OpenAICompatibleProvider(endpoint, api_key, model)
    raise AIProviderError(f"Fournisseur IA inconnu : {provider_name}.")
