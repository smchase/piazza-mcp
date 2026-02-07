# Piazza MCP Server — Project Context

## What This Is

An MCP server that lets AI agents browse a user's Piazza course forum — searching posts, reading questions/answers, and discovering relevant course content to assist with coursework.

## Architecture

`src/` layout with `uv` for dev and running. Three files:

- `server.py` — FastMCP server with 4 tools, startup auth, class state management, tool descriptions
- `formatting.py` — html2text wrapper, snippet generation, post/answer/followup formatting
- `pyproject.toml` — Metadata, deps, `[project.scripts]` entry point

## Authentication

Env vars: `PIAZZA_EMAIL`, `PIAZZA_PASSWORD`. Server calls `Piazza.user_login()` once on startup.

## Design Decisions

### Tool Design (4 tools)

**`list_classes()`** — Returns only **active** enrolled classes: name, term, course number, network ID. Filters out old/inactive classes via the `status` field from Piazza's `user.status` API. Does **not** show which class is currently active in the server — the agent always treats it as a fresh start and must select a class. This ensures the agent always follows the same predictable flow: list → select → search.

**`set_class(network_id)`** — Sets the active class and returns class name/term (confirmation) plus list of all available folders/tags. Called once at the start of a session before any searching. The agent doesn't know whether a class is already active, so it always calls this — which is the desired behavior.

Folder names matter because naming isn't predictable — "assignment 1" might be "hw1", "a1", or "problem_set_1". The agent needs to see the actual folder names to map user intent to the right filter.

**`search_posts(query, folder, limit)`** — Unified search/browse tool. Three modes:
- No args: recent posts (feed/browse mode)
- query only: keyword search across all posts
- folder only: all posts in a specific folder
- both: keyword search filtered to a folder (search API → client-side folder filter)

Returns per result: post number (`@123`), subject, snippet (~150 chars), folders/tags, answer status (instructor/student/unanswered), type, date.

**`get_post(post_number)`** — Full post content formatted as readable markdown: subject and body, instructor answer (if any), student answer (if any) with endorsement status, all follow-up discussions with replies (no truncation), folders, date.

### Agent Tool Descriptions

The docstrings on each tool are carefully written to guide the agent's behavior. Key points embedded in descriptions:
- `list_classes`: Agent should use context clues to pick the right class, ask user if ambiguous
- `set_class`: Agent must call this once before search/get_post; should check folder names carefully
- `search_posts`: Prefer folder filtering for assignment-specific content; keyword search doesn't search folder names; keyword search requires ALL keywords to match so keep queries to 1-2 words max
- `get_post`: Use post number from search results or user reference like '@142'

### State Management

From the agent's perspective, every conversation looks the same — it doesn't know if a class is already active. The server hides this state.

**Every conversation (agent's view is identical):**
```
list_classes() → sees enrolled classes (no active indicator)
→ set_class("abc123") for the right class (inferred or asked)
→ gets folders: ["hw1", "hw2", "hw3", "midterm", "logistics"]
→ search_posts(folder="hw3") or search_posts(query="late policy")
→ get_post(142) → reads full content
```

**What happens internally:**
- `set_class` creates a Network connection and fetches class metadata from `user.status`
- Subsequent `search_posts`/`get_post` calls use the stored Network object

## Content Formatting (`formatting.py`)

Uses `html2text` for HTML-to-markdown. All text fields go through entity decoding (`html.unescape`) — post subjects in both search results and full posts, snippets via `make_snippet()`, and body content via `html_to_markdown()`. The Piazza API returns only post content HTML (no page chrome), so html2text works well without a custom parser.

The module handles:
- Post body HTML → readable markdown (via html2text)
- HTML entity decoding on all text fields (subjects, snippets, content)
- Extracting nested answer/followup structure from raw API response (the `children` field in Piazza's JSON)
- Snippet generation: strip HTML tags, decode entities, collapse whitespace, truncate to ~150 chars
- Building formatted output for both search result summaries and full post views

## Verification Checklist

1. `uv run piazza-mcp` starts without errors
2. `list_classes()` returns only active enrolled courses (no active class indicator)
3. `set_class()` returns class name + folder list
4. `search_posts()` with no args returns recent feed
5. `search_posts(folder="hw1")` returns folder-filtered results with snippets
6. `search_posts(query="deadline")` returns keyword matches
7. `search_posts(query="extension", folder="hw1")` returns combined results
8. `get_post(N)` returns readable markdown with all answers and followups

## Future Improvements

- **Better distribution**: Publish to PyPI (`uv build && uv publish`) so installation is just `uv tool install piazza-mcp` instead of cloning a repo. The `pyproject.toml` already supports this.
