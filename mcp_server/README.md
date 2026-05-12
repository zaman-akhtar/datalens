# DataLens MCP Server

Exposes the DataLens query engine to Claude Desktop (and any MCP client) via
the Model Context Protocol. The same three tools that power the in-app LLM
chat are available: `query_data`, `get_column_statistics`, `generate_chart`,
plus a `list_datasets_tool` for dataset discovery.

## Prerequisites

- DataLens backend dependencies installed (`uv sync --extra dev` from the
  project root)
- A populated DataLens database (run the frontend, upload at least one CSV)

## Connect to Claude Desktop

Add the following block to your Claude Desktop config file:

**macOS** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "datalens": {
      "command": "uv",
      "args": ["run", "mcp_server/server.py"],
      "cwd": "C:/datalens",
      "env": {
        "DATABASE_URL": "sqlite:///./datalens.db"
      }
    }
  }
}
```

Replace `C:/datalens` with the actual path to your DataLens project root.
Set `DATABASE_URL` to point at the same database file the backend uses
(default: `datalens.db` in the project root).

## Usage

After connecting, ask Claude:

```
List my datasets.
```

Claude calls `list_datasets_tool` and returns available dataset IDs. Then:

```
What are the top 5 transaction categories by count in dataset <id>?
```

Claude calls `query_data` with `x="category", agg="count", limit=5`.

```
Show me the distribution of transaction amounts.
```

Claude calls `generate_chart` with `chart_type="histogram", x="amt"`.

## Tools

| Tool | Description |
|---|---|
| `list_datasets_tool` | List all datasets in the database |
| `query_data` | Structured aggregation (GROUP BY + agg function) |
| `get_column_statistics` | Descriptive stats for one column |
| `generate_chart` | Return a ChartSpec the frontend can render |

## Run manually (for debugging)

```bash
uv run mcp_server/server.py
```

The server speaks MCP over stdio and is ready for any MCP client.
