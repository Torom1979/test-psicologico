# tests_psicologicos/templatetags/custom_filters.py
from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key))


@register.filter
def get_disc_item(dictionary, key_tipo):
    """
    Permite acceder a respuestas DISC anidadas como '77.mas' o '78.menos'
    """
    try:
        key, subkey = key_tipo.split(".")
        return dictionary.get(str(key), {}).get(subkey)
    except:
        return None

