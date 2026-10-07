from django import template


register = template.Library()
BADGES = {
    "active": "chip chip-active",
    "graduated": "chip chip-graduated",
    "suspended": "chip chip-suspended",
    "withdrawn": "chip chip-withdrawn",
}


@register.filter
def badge_classes(status):
    return BADGES.get(status, BADGES["withdrawn"])


@register.filter
def split(value, separator=","):
    return value.split(separator)


@register.filter
def lookup(mapping, key):
    return mapping.get(key, 0) if mapping else 0


@register.filter
def avatar_tone(pk):
    return ""


@register.filter
def initials(person):
    return f"{person.first_name[:1]}{person.last_name[:1]}".upper() or person.username[:2].upper()


@register.simple_tag
def query_string(request, **kwargs):
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value
    # Always return a "?..." form so htmx treats it as a query string, not a path.
    return "?" + params.urlencode()


@register.simple_tag
def page_numbers(page):
    start = max(1, min(page.number - 2, page.paginator.num_pages - 4))
    return range(start, min(page.paginator.num_pages + 1, start + 5))


@register.inclusion_tag("ui/_sort_header.html", takes_context=True)
def sort_header(context, field, label, css=""):
    sort = context.get("sort", "name")
    active = sort.lstrip("-") == field
    return {"request": context["request"], "label": label, "css": css, "active": active,
            "next_sort": f"-{field}" if sort == field else field,
            "icon": "ti-arrow-down" if sort.startswith("-") else "ti-arrow-up"}
