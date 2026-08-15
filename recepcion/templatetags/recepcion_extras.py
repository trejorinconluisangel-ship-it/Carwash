from django import template

register = template.Library()


@register.filter
def dictget(diccionario, clave):
    if not diccionario:
        return []
    return diccionario.get(clave, [])
