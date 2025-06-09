"""
Localization messages for ChapterRandomizer
"""

MESSAGES = {
    'es': {
        'NO_VLC': "No se pudo encontrar VLC. Por favor checkeá que esté bien instalado.",
        'NO_VALID_FILES': "La carpeta especificada no contiene ningún archivo válido. Por favor intente de nuevo",
        'NOSTALGIA': "¿Activar nostalgia?",
        'PLAYBACK_ERR': "Error en la reproducción del contenido. Validar logs de VLC para ver los detalles."
    },
    'en': {
        'NO_VLC': "Failed to detect VLC. Please check it's properly installed.",
        'NO_VALID_FILES': "The specified path does not contain any playable files. Please try again.",
        'NOSTALGIA': "Enable nostalgia? (Note this will make sense for Arg people mostly)",
        'PLAYBACK_ERR': "Error while trying to play content. Check VLC logs for further details."
    }
}

def get_message(key, lang='en'):
    """
    Get a localized message for the given key and language.
    Falls back to English if the requested language or key is not found.
    """
    return MESSAGES.get(lang, MESSAGES['en']).get(key, MESSAGES['en'].get(key, f"Missing message: {key}")) 