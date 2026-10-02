from django import template


register = template.Library()
BADGES = {
    "active": "bg-azure-500/10 text-azure-300 ring-azure-500/30",
    "graduated": "bg-gold-400/10 text-gold-300 ring-gold-400/30",
    "suspended": "bg-lavender-400/10 text-lavender-300 ring-lavender-400/30",
    "withdrawn": "bg-ink-700/60 text-ink-200 ring-ink-600",
}
TONES = ["bg-azure-500/15 text-azure-300", "bg-lavender-400/15 text-lavender-300", "bg-gold-400/15 text-gold-300"]


@register.filter
def badge_classes(status):
    return BADGES.get(status, BADGES["withdrawn"])


@register.filter
def avatar_tone(pk):
    return TONES[int(pk or 0) % 3]


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
    return params.urlencode()


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
