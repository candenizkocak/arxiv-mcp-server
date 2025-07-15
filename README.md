# Research Papers MCP Server

[![smithery badge](https://smithery.ai/badge/@candenizkocak/research-papers-mcp-server)](https://smithery.ai/server/@candenizkocak/research-papers-mcp-server)

This project is a Model Context Protocol (MCP) server written in Python that acts as an intelligent interface to academic paper repositories, particularly the arXiv API. It allows Large Language Models (LLMs) like Claude to search for and retrieve academic papers.

## Features

This server exposes a suite of tools to the LLM, enabling it to:

-   **`search_papers`**: Perform a general topic search for papers from sources like arXiv.
-   **`find_papers_by_author`**: Find recent papers by a specific author from sources like arXiv.
-   **`get_latest_from_category`**: Browse the newest submissions in a given arXiv category (e.g., `cs.LG`).
-   **`get_paper_by_id`**: Get full details for a single paper by its arXiv ID.
-   **`get_papers_by_ids`**: Efficiently get details for a list of papers by their arXiv IDs.

## Requirements

-   Python 3.10+
-   [uv](https://github.com/astral-sh/uv) (for environment and package management)
-   An MCP Host like [Claude for Desktop](https://www.claude.ai/download)

## Setup and Installation

### Installing via Smithery

To install this research papers MCP server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@candenizkocak/research-papers-mcp-server):

```bash
npx -y @smithery/cli install @candenizkocak/research-papers-mcp-server --client claude
```

### Manual Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/candenizkocak/research-papers-mcp-server.git research-papers-mcp-server
    cd research-papers-mcp-server
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
    uv sync
    ```
    *(Note: `uv sync` will install dependencies from the `pyproject.toml` file).*

## Usage with Claude for Desktop

1.  Find the absolute path to your `research-papers-mcp-server` directory.

2.  Open your Claude for Desktop configuration file (`claude_desktop_config.json`):
    -   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
    -   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

3.  Add the server configuration, replacing the placeholder with your absolute path:

    ```json
    {
      "mcpServers": {
        "research-papers": {
          "command": "uv",
          "args": [
            "--directory",
            "/ABSOLUTE/PATH/TO/research-papers-mcp-server",
            "run",
            "arxiv_server.py"
          ]
        }
      }
    }
    ```

4.  Completely restart Claude for Desktop.

## Example Prompts

-   **General Search**: "Find papers about 'mixture of experts models'."
-   **Author Search**: "What are the most recent papers by Geoffrey Hinton?"
-   **Category Search**: "What's new in the cs.LG category on arXiv?"
-   **Single ID Lookup**: "Tell me about arXiv paper 1706.03762."
-   **Multiple ID Lookup**: "Give me details for papers 2307.09288 and 2203.02155."

## Acknowledgements

Thank you to arXiv for use of its open access interoperability.

## Compliance Notes

Developers and users of this project are responsible for familiarizing themselves with the official [arXiv API Terms of Use](https://arxiv.org/help/api/tou.html), [API Basics](https://arxiv.org/help/api/basics.html), and [API User Manual](https://arxiv.org/help/api/user-manual.html) to ensure full compliance with arXiv's policies, including any rate limits or usage restrictions.
