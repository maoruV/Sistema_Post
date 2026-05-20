from django import template

register = template.Library()


@register.filter
def pesos(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return '$0'
    return f'${value:,.0f}'


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    request = context['request']
    dict_ = request.GET.copy()
    for k, v in kwargs.items():
        dict_[k] = v
    return dict_.urlencode()
