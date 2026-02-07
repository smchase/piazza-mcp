import html2text
import re


_converter = html2text.HTML2Text()
_converter.body_width = 0
_converter.ignore_images = True
_converter.ignore_links = False
_converter.unicode_snob = True


def html_to_markdown(html: str) -> str:
    """Convert HTML content to readable markdown."""
    if not html:
        return ""
    return _converter.handle(html).strip()


def make_snippet(html: str, max_length: int = 150) -> str:
    """Strip HTML tags, collapse whitespace, and truncate to a snippet."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_length:
        return text[:max_length].rstrip() + "..."
    return text


def format_search_result(post: dict) -> str:
    """Format a single post for search result display."""
    nr = post.get("nr", "?")
    subject = post.get("history", [{}])[0].get("subject", "(no subject)") if post.get("history") else "(no subject)"
    content_html = post.get("history", [{}])[0].get("content", "") if post.get("history") else ""
    snippet = make_snippet(content_html)
    folders = ", ".join(post.get("folders", []))
    has_i_answer = post.get("type") == "question" and bool(post.get("children", []) and any(
        c.get("type") == "i_answer" for c in post.get("children", [])
    ))
    created = post.get("created", "")

    lines = [f"### @{nr}: {subject}"]
    if snippet:
        lines.append(snippet)
    parts = []
    if folders:
        parts.append(f"Folders: {folders}")
    if has_i_answer:
        parts.append("Has instructor answer")
    if created:
        parts.append(f"Date: {created}")
    if parts:
        lines.append(" | ".join(parts))
    return "\n".join(lines)


def _format_answer(child: dict, label: str) -> str:
    """Format an instructor or student answer."""
    history = child.get("history", [])
    if not history:
        return ""
    content_html = history[0].get("content", "")
    content = html_to_markdown(content_html)
    if not content:
        return ""

    endorsed = ""
    if child.get("tag_endorse"):
        endorsers = child["tag_endorse"]
        endorsed = f" (endorsed by {len(endorsers)} user{'s' if len(endorsers) != 1 else ''})"

    return f"## {label}{endorsed}\n\n{content}"


def _format_followup(child: dict) -> str:
    """Format a follow-up discussion and its replies."""
    subject = child.get("subject", "")
    content = html_to_markdown(subject)
    if not content:
        return ""

    lines = [f"- **Follow-up:** {content}"]

    for reply in child.get("children", []):
        reply_content = html_to_markdown(reply.get("subject", ""))
        if reply_content:
            lines.append(f"  - **Reply:** {reply_content}")

    return "\n".join(lines)


def format_full_post(post: dict) -> str:
    """Format a complete post with all answers and follow-ups."""
    nr = post.get("nr", "?")
    history = post.get("history", [])
    subject = history[0].get("subject", "(no subject)") if history else "(no subject)"
    content_html = history[0].get("content", "") if history else ""
    content = html_to_markdown(content_html)
    folders = ", ".join(post.get("folders", []))
    created = post.get("created", "")
    post_type = post.get("type", "note")

    lines = [f"# @{nr}: {subject}"]

    meta_parts = []
    if post_type:
        meta_parts.append(f"Type: {post_type}")
    if folders:
        meta_parts.append(f"Folders: {folders}")
    if created:
        meta_parts.append(f"Date: {created}")
    if meta_parts:
        lines.append(" | ".join(meta_parts))

    if content:
        lines.append("")
        lines.append(content)

    children = post.get("children", [])

    i_answer = next((c for c in children if c.get("type") == "i_answer"), None)
    if i_answer:
        formatted = _format_answer(i_answer, "Instructor Answer")
        if formatted:
            lines.append("")
            lines.append(formatted)

    s_answer = next((c for c in children if c.get("type") == "s_answer"), None)
    if s_answer:
        formatted = _format_answer(s_answer, "Student Answer")
        if formatted:
            lines.append("")
            lines.append(formatted)

    followups = [c for c in children if c.get("type") == "followup"]
    if followups:
        lines.append("")
        lines.append("## Follow-up Discussions")
        lines.append("")
        for fu in followups:
            formatted = _format_followup(fu)
            if formatted:
                lines.append(formatted)

    return "\n".join(lines)
