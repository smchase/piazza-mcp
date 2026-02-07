import html
import os

from fastmcp import FastMCP
from piazza_api import Piazza
from piazza_api.network import FolderFilter, Network

from piazza_mcp.formatting import format_full_post, make_snippet

mcp = FastMCP("piazza")

# Global state
_piazza: Piazza | None = None
_network: Network | None = None


def _login() -> Piazza:
    """Authenticate with Piazza using environment variables."""
    global _piazza
    if _piazza is not None:
        return _piazza
    email = os.environ.get("PIAZZA_EMAIL")
    password = os.environ.get("PIAZZA_PASSWORD")
    if not email or not password:
        raise RuntimeError(
            "PIAZZA_EMAIL and PIAZZA_PASSWORD environment variables are required"
        )
    p = Piazza()
    p.user_login(email=email, password=password)
    _piazza = p
    return p


def _get_network() -> Network:
    """Return the active Network, or raise if none is set."""
    if _network is None:
        raise RuntimeError("No class selected. Call set_class(network_id) first.")
    return _network


@mcp.tool()
def list_classes() -> str:
    """Call this first to see your enrolled Piazza classes. Only active classes
    are shown. You must then call set_class with the appropriate network_id
    before you can search or read posts. Use context clues (project directory,
    what the user is asking about, class name/number) to determine the right
    class. If it's obvious from context, proceed. If ambiguous, ask the user
    which class they mean."""
    p = _login()
    status = p.get_user_status()
    raw_classes = status.get("networks", [])
    if not raw_classes:
        return "No enrolled classes found."
    # Filter to only active classes
    active = [c for c in raw_classes if c.get("status") == "active"]
    if not active:
        return "No active classes found."
    lines = []
    for c in active:
        name = c.get("name", "Unknown")
        term = c.get("term", "")
        num = c.get("course_number", "")
        nid = c.get("id", "")
        line = f"- **{name}**"
        if num:
            line += f" ({num})"
        if term:
            line += f" — {term}"
        line += f"\n  network_id: `{nid}`"
        lines.append(line)
    return "\n".join(lines)


@mcp.tool()
def set_class(network_id: str) -> str:
    """Select a class to work with. Must be called once before searching or
    reading posts. Returns the list of available folders — check these carefully
    since folder names may not match what the user calls things (e.g.,
    'assignment 1' might be folder 'hw1')."""
    global _network

    p = _login()

    # Get class name and folders from user.status — each network object has
    # "folders" directly (the feed endpoint doesn't reliably include them)
    status = p.get_user_status()
    networks = status["networks"]
    matched = [c for c in networks if c["id"] == network_id]
    if not matched:
        raise RuntimeError(f"network_id '{network_id}' not found in enrolled classes")

    _network = p.network(network_id)
    class_info = matched[0]
    name = class_info.get("name", "")
    term = class_info.get("term", "")
    class_name = f"{name} — {term}" if term else name
    folders = class_info.get("folders", [])

    lines = [f"Active class: **{class_name}**", "", "Available folders:"]
    for f in folders:
        lines.append(f"- {f}")
    if not folders:
        lines.append("(no folders found)")
    return "\n".join(lines)


@mcp.tool()
def search_posts(
    query: str | None = None,
    folder: str | None = None,
    limit: int = 20,
) -> str:
    """Search for posts by keyword, filter by folder, or both. Call with no
    arguments to browse recent posts. Use folder names from the set_class
    response. Prefer folder filtering when looking for assignment-specific
    content since keyword search doesn't search folder names. Combine folder +
    query to narrow within a topic.

    IMPORTANT: Keyword search requires ALL keywords to appear in a result —
    if any keyword is missing, the post won't match. Keep queries to 1-2 words
    max. Use the most specific single keyword likely to appear verbatim in
    posts. Run multiple short searches rather than one long query."""
    network = _get_network()

    # search_feed returns a plain list of post dicts.
    # get_feed and get_filtered_feed return {"feed": [...]}.
    if query and folder:
        results = network.search_feed(query)
        posts = [p for p in results if folder in p.get("folders", [])][:limit]
    elif query:
        posts = network.search_feed(query)[:limit]
    elif folder:
        posts = network.get_filtered_feed(FolderFilter(folder))["feed"][:limit]
    else:
        posts = network.get_feed(limit=limit, offset=0)["feed"][:limit]

    if not posts:
        return "No posts found."

    lines = [f"Found {len(posts)} post(s):", ""]
    for post_summary in posts:
        nr = post_summary.get("nr", post_summary.get("id", "?"))
        subject = html.unescape(post_summary.get("subject", "(no subject)"))
        snippet = make_snippet(post_summary.get("content_snipet", ""))
        folders_list = ", ".join(post_summary.get("folders", []))
        modified = post_summary.get("modified", "")
        post_type = post_summary.get("type", "")
        has_i = post_summary.get("has_i")
        has_s = post_summary.get("has_s")
        no_answer = post_summary.get("no_answer")

        line = f"### @{nr}: {subject}"
        if snippet:
            line += f"\n{snippet}"
        meta = []
        if folders_list:
            meta.append(f"Folders: {folders_list}")
        if has_i:
            meta.append("Has instructor answer")
        if has_s:
            meta.append("Has student answer")
        if no_answer:
            meta.append("Unanswered")
        if post_type:
            meta.append(f"Type: {post_type}")
        if modified:
            meta.append(f"Date: {modified}")
        if meta:
            line += "\n" + " | ".join(meta)
        lines.append(line)

    return "\n\n".join(lines)


@mcp.tool()
def get_post(post_number: int) -> str:
    """Get the full content of a specific post including all answers and
    follow-up discussions. Use the post number from search results or from a
    user reference like '@142'."""
    network = _get_network()
    post = network.get_post(post_number)
    return format_full_post(post)


def main():
    """Entry point for the piazza-mcp command."""
    _login()
    mcp.run()
