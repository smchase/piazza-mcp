import html
import re

import html2text

_converter = html2text.HTML2Text()
_converter.body_width = 0
_converter.ignore_images = True
_converter.ignore_links = False
_converter.unicode_snob = True


def html_to_markdown(raw_html: str) -> str:
    """Convert HTML content to readable markdown."""
    if not raw_html:
        return ""
    return _converter.handle(raw_html).strip()


def make_snippet(text: str, max_length: int = 150) -> str:
    """Strip HTML tags, decode entities, collapse whitespace, and truncate."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_length:
        return text[:max_length].rstrip() + "..."
    return text


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
        count = len(child["tag_endorse"])
        s = "s" if count != 1 else ""
        endorsed = f" (endorsed by {count} user{s})"

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
    raw_subject = (
        history[0].get("subject", "(no subject)") if history else "(no subject)"
    )
    subject = html.unescape(raw_subject)
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
