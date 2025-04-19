# Web Search MCP Server

This project implements a Model Context Protocol (MCP) server that provides tools for web searching and content processing. It leverages the Brave Search API for web searches, fetches web page content, converts it to Markdown, and uses an AI assistant (powered by OpenAI) to trim content based on relevance to a given context, to reduce context usage.

## Features (MCP Tools)

The server exposes the following tools for use by an MCP client:

1.  **`search_web`**:
    
    Searches the web using Brave Search and returns formatted search results (title, URL, description).
    *   Input: `query` (string) - The search query.
    *   Output: Markdown formatted list of search results.

2.  **`pretty_page`**:
    
    Fetches the content of a given URL and converts it to Markdown format.
    *   Input: `url` (string) - The URL of the web page.
    *   Output: Markdown content of the page, or an error message.

3.  **`search_process_pages`**:
    
    Performs a web search, fetches the content of each result URL, converts it to Markdown, and then uses an AI assistant to trim the content, keeping only the parts relevant to the provided context.
    *   Input:
        *   `query` (string) - The search query.
        *   `context` (string) - Descriptive context used by the AI to determine relevant sections of the page content.
    *   Output: A concatenated string containing the title, URL, and AI-trimmed Markdown content for each search result, separated by `################`.
