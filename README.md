# piazza-mcp

An MCP server that lets AI agents browse your Piazza course forums — search posts, read questions/answers, and discover relevant course content.

## Install

Requires [uv](https://docs.astral.sh/uv/) (`brew install uv`).

### Claude Code

```bash
claude mcp add --scope user piazza --env PIAZZA_EMAIL=you@school.ca --env PIAZZA_PASSWORD=your-password -- uvx piazza-mcp@latest
```

### VS Code

Add to `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "piazza": {
        "command": "uvx",
        "args": ["piazza-mcp@latest"],
        "env": {
          "PIAZZA_EMAIL": "you@school.ca",
          "PIAZZA_PASSWORD": "your-password"
        }
      }
    }
  }
}
```

Credentials are your Piazza login email and password.

## Tools

| Tool | Description |
|------|-------------|
| `list_classes()` | List active enrolled Piazza classes |
| `set_class(network_id)` | Select a class, get available folders |
| `search_posts(query, folder, limit)` | Search by keyword, folder, or both |
| `get_post(post_number)` | Read full post with answers and follow-ups |

## Development

```bash
git clone https://github.com/smchase/piazza-mcp
cd piazza-mcp
uv sync --group dev
```

Use a local clone in your MCP client:

```bash
claude mcp add piazza-dev --env PIAZZA_EMAIL=you@school.ca --env PIAZZA_PASSWORD=your-password -- uv --directory /path/to/piazza-mcp run piazza-mcp
```
