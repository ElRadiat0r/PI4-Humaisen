import os

from django.core.exceptions import ValidationError

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 Mo
MAX_ATTACHMENTS_PER_PROJECT = 10
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".csv", ".docx", ".xlsx"}


def validate_attachment_size(file):
    if file.size > MAX_ATTACHMENT_SIZE:
        raise ValidationError(
            f"Fichier trop volumineux (max {MAX_ATTACHMENT_SIZE // (1024 * 1024)} Mo)."
        )


def validate_attachment_extension(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Type de fichier non autorisé. Autorisés : {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )


def validate_attachment(file):
    validate_attachment_size(file)
    validate_attachment_extension(file)


def validate_consents(data_processing: bool, ai_analysis: bool):
    """Le consentement IA n'a de sens que si le traitement des données est accepté."""
    if ai_analysis and not data_processing:
        raise ValidationError(
            "Le consentement à l'analyse IA nécessite le consentement au traitement des données."
        )
