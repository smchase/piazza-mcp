import os

from fastmcp import FastMCP
from piazza_api import Piazza
from piazza_api.network import Network, FolderFilter

from piazza_mcp.formatting import format_full_post

mcp = FastMCP("piazza")

# Global state
_piazza: Piazza | None = None
_network: Network | None = None
_network_id: str | None = None
_folders: list[str] | None = None


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
        raise RuntimeError(
            "No class selected. Call set_class(network_id) first."
        )
    return _network


@mcp.tool()
def list_classes() -> str:
    """Call this first to see your enrolled Piazza classes. You must then call
    set_class with the appropriate network_id before you can search or read
    posts. Use context clues (project directory, what the user is asking about,
    class name/number) to determine the right class. If it's obvious from
    context, proceed. If ambiguous, ask the user which class they mean."""
    p = _login()
    classes = p.get_user_classes()
    if not classes:
        return "No enrolled classes found."
    lines = []
    for c in classes:
        name = c.get("name", "Unknown")
        term = c.get("term", "")
        num = c.get("num", "")
        nid = c.get("nid", "")
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
    """Select a class to work with. Must be called before searching or reading
    posts. Returns the list of available folders — check these carefully since
    folder names may not match what the user calls things (e.g., 'assignment 1'
    might be folder 'hw1'). You must call this every time before using
    search_posts or get_post."""
    global _network, _network_id, _folders

    p = _login()

    # If same class is already set, return cached state
    if _network_id == network_id and _network is not None and _folders is not None:
        lines = [f"Class already active: **{network_id}**", "", "Available folders:"]
        for f in _folders:
            lines.append(f"- {f}")
        return "\n".join(lines)

    network = p.network(network_id)
    _network = network
    _network_id = network_id

    # Fetch class info and folders from feed metadata
    feed = network.get_feed(limit=1, offset=0)
    folders = feed.get("feed", {}).get("folders", [])
    _folders = folders

    # Try to get class name from user classes
    class_name = network_id
    try:
        classes = p.get_user_classes()
        for c in classes:
            if c.get("nid") == network_id:
                name = c.get("name", "")
                term = c.get("term", "")
                class_name = f"{name} — {term}" if term else name
                break
    except Exception:
        pass

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
    query to narrow within a topic."""
    network = _get_network()

    if query and folder:
        # Search then filter client-side by folder
        results = network.search_feed(query)
        posts = [
            p for p in results.get("feed", [])
            if folder in p.get("folders", [])
        ][:limit]
    elif query:
        results = network.search_feed(query)
        posts = results.get("feed", [])[:limit]
    elif folder:
        results = network.get_filtered_feed(FolderFilter(folder))
        posts = results.get("feed", [])[:limit]
    else:
        results = network.get_feed(limit=limit, offset=0)
        posts = results.get("feed", [])[:limit]

    if not posts:
        return "No posts found."

    # Feed results are partial — fetch full posts for proper formatting
    lines = [f"Found {len(posts)} post(s):", ""]
    for post_summary in posts:
        nr = post_summary.get("nr", post_summary.get("id", "?"))
        subject = post_summary.get("subject", "(no subject)")
        snippet = post_summary.get("content_snipet", "")  # Piazza's typo
        if not snippet:
            snippet = ""
        folders_list = ", ".join(post_summary.get("folders", []))
        has_i_answer = bool(post_summary.get("i_answer"))
        created = post_summary.get("created", post_summary.get("modified", ""))
        post_type = post_summary.get("type", "")

        line = f"### @{nr}: {subject}"
        parts = []
        if snippet:
            parts.append(snippet[:150] + ("..." if len(snippet) > 150 else ""))
        meta = []
        if folders_list:
            meta.append(f"Folders: {folders_list}")
        if has_i_answer:
            meta.append("Has instructor answer")
        if post_type:
            meta.append(f"Type: {post_type}")
        if created:
            meta.append(f"Date: {created}")

        if parts:
            line += "\n" + parts[0]
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


if __name__ == "__main__":
    main()
