import httpx
import feedparser
import urllib.parse
from mcp.server.fastmcp import FastMCP
from typing import List

mcp = FastMCP("arxiv")

ARXIV_API_BASE = "http://export.arxiv.org/api/query?"
USER_AGENT = "mcp-arxiv-server/1.0"

def _format_single_paper_details(entry: feedparser.FeedParserDict) -> str:
    """Helper function to format the details of a single paper entry."""
    title = entry.title.replace('\n', ' ')
    authors = ", ".join(author.name for author in entry.authors)
    abstract_link = entry.id
    pdf_link = next((link.href for link in entry.links if link.rel == 'related' and link.type == 'application/pdf'), 'N/A')
    summary = entry.summary.replace('\n', ' ')
    
    published_date = entry.published_parsed or entry.updated_parsed
    date_str = f"{published_date.tm_year}-{published_date.tm_mon:02d}-{published_date.tm_mday:02d}" if published_date else "N/A"
    
    primary_category = entry.get('arxiv_primary_category', {}).get('term', 'N/A')
    
    return f"""
Title: {title}
Authors: {authors}
Published Date: {date_str}
Primary Category: {primary_category}
Abstract Link: {abstract_link}
PDF Link: {pdf_link}

Abstract:
{summary}
""".strip()


@mcp.tool()
async def search_papers(
    query: str, max_results: int = 5, sort_by: str = "submittedDate", sort_order: str = "descending"
) -> str:
    """
    General purpose search for arXiv papers. Best for complex queries.
    Args:
        query: Search query using arXiv syntax (e.g., 'ti:"quantum computing" AND au:"John Preskill"').
        max_results: Max number of papers to return.
        sort_by: Sort order ('relevance', 'lastUpdatedDate', 'submittedDate').
        sort_order: Sort direction ('ascending', 'descending').
    """
    params = { "search_query": query, "start": 0, "max_results": max_results, "sortBy": sort_by, "sortOrder": sort_order }
    url = f"{ARXIV_API_BASE}{urllib.parse.urlencode(params)}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=30.0)
    if response.status_code != 200: return f"Error: arXiv API returned status {response.status_code}"
    feed = feedparser.parse(response.text)
    if not feed.entries: return "No papers found for your query."
    formatted_papers = []
    for i, entry in enumerate(feed.entries):
        paper_details = _format_single_paper_details(entry)
        abstract_index = paper_details.find("Abstract:")
        short_paper_details = paper_details[:abstract_index] + f"Abstract: {entry.summary.replace('\n', ' ')[:250]}..."
        formatted_papers.append(f"{i+1}. {short_paper_details}")
    return f"Found {len(feed.entries)} papers:\n" + "\n\n---\n\n".join(formatted_papers)

@mcp.tool()
async def find_papers_by_author(author_name: str, max_results: int = 5) -> str:
    """
    Finds recent papers by a specific author's name.
    Args:
        author_name: The full name of the author to search for (e.g., "Geoffrey Hinton").
        max_results: Max number of papers to return.
    """
    query = f'au:"{author_name}"'
    return await search_papers(query=query, max_results=max_results, sort_by="submittedDate", sort_order="descending")

@mcp.tool()
async def get_latest_from_category(category: str, max_results: int = 5) -> str:
    """
    Gets the most recently submitted papers from a specific arXiv category.
    Args:
        category: The category code to search (e.g., 'cs.LG', 'astro-ph.CO').
        max_results: Max number of papers to return.
    """
    query = f'cat:{category}'
    return await search_papers(query=query, max_results=max_results, sort_by="submittedDate", sort_order="descending")

@mcp.tool()
async def get_paper_by_id(arxiv_id: str) -> str:
    """Retrieves full details for a single paper using its arXiv ID."""
    return await get_papers_by_ids([arxiv_id])

@mcp.tool()
async def get_papers_by_ids(arxiv_ids: List[str]) -> str:
    """
    Retrieves full details for a list of papers using their arXiv IDs.
    Args:
        arxiv_ids: A list of arXiv IDs (e.g., ['2307.09288', '1706.03762']).
    """
    id_string = ",".join(arxiv_ids)
    params = {"id_list": id_string, "max_results": len(arxiv_ids)}
    url = f"{ARXIV_API_BASE}{urllib.parse.urlencode(params)}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=30.0)
    if response.status_code != 200: return f"Error: arXiv API returned status {response.status_code}"
    feed = feedparser.parse(response.text)
    if not feed.entries: return f"Could not find any papers with the provided IDs."
    
    all_details = [_format_single_paper_details(entry) for entry in feed.entries]
    return "\n\n---\n\n".join(all_details)


if __name__ == "__main__":
    mcp.run(transport='stdio')