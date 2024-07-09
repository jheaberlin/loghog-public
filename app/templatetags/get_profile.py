from django import template
from libgravatar import Gravatar

register = template.Library()

@register.filter
def get_profile(email) -> str:
    g = Gravatar(email)
    return g.get_image()
    