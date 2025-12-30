def format_span(span):
    if not span:
        return ""
    return f"{span.start.line}:{span.start.col}"