
import os

from django.core.exceptions import ValidationError


MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
MAX_ATTACHMENTS_PER_PROJECT = 10

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".csv",
    ".docx",
    ".xlsx",
}


def validate_attachment_size(file):
    if file.size > MAX_ATTACHMENT_SIZE:
        raise ValidationError(
            f"Fichier trop volumineux "
            f"(maximum {MAX_ATTACHMENT_SIZE // (1024 * 1024)} Mo)."
        )

    if file.size == 0:
        raise ValidationError("Le fichier est vide.")


def validate_attachment_extension(file):
    ext = os.path.splitext(file.name)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            "Type de fichier non autorisé. "
            f"Extensions autorisées : "
            f"{', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )


def validate_attachment(file):
    validate_attachment_size(file)
    validate_attachment_extension(file)


def validate_consents(data_processing: bool, ai_analysis: bool):
    if ai_analysis and not data_processing:
        raise ValidationError(
            "Le consentement à l'analyse IA nécessite "
            "le consentement au traitement des données."
        )
