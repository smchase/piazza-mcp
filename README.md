# piazza-mcp

An MCP server that lets AI agents browse your Piazza course forums — search posts, read questions/answers, and discover relevant course content.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

Add to your Claude Code MCP config (`~/.claude.json` or project settings):

```json
{
  "mcpServers": {
    "piazza": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/piazza-mcp", "piazza-mcp"],
      "env": {
        "PIAZZA_EMAIL": "you@school.edu",
        "PIAZZA_PASSWORD": "your-password"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `list_classes()` | List all enrolled Piazza classes |
| `set_class(network_id)` | Select a class, get available folders |
| `search_posts(query, folder, limit)` | Search by keyword, folder, or both |
| `get_post(post_number)` | Read full post with answers and follow-ups |

## Dependencies

- [fastmcp](https://github.com/jlowin/fastmcp) — MCP server framework
- [piazza-api](https://github.com/hfaran/piazza-api) — Unofficial Piazza API client
- [html2text](https://github.com/Alir3z4/html2text) — HTML to markdown conversion
