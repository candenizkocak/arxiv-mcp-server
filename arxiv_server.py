import httpx
import feedparser
import urllib.parse
from mcp.server.fastmcp import FastMCP
from typing import List, Any
import asyncio

mcp = FastMCP("research-papers-mcp") # Changed internal MCP instance name

ARXIV_API_BASE = "https://export.arxiv.org/api/query?"
USER_AGENT = "mcp-research-papers-server/1.0" # Changed User-Agent name

def _format_single_paper_details(entry: feedparser.FeedParserDict) -> str:
    """Helper function to format the details of a single paper entry."""
    # Ensure all fields are handled gracefully if they don't exist
    title = entry.title.replace('\n', ' ') if hasattr(entry, 'title') else 'N/A'
    authors = ", ".join(author.name for author in entry.authors) if hasattr(entry, 'authors') else 'N/A'
    
    # Extract arXiv ID from entry.id (e.g., http://arxiv.org/abs/hep-ex/0307015 -> hep-ex/0307015)
    arxiv_id_match = entry.id.split('/')[-1] if hasattr(entry, 'id') else 'N/A'
    
    abstract_link = entry.id if hasattr(entry, 'id') else 'N/A'
    pdf_link = next((link.href for link in entry.links if link.rel == 'related' and link.type == 'application/pdf'), 'N/A') if hasattr(entry, 'links') else 'N/A'
    summary = entry.summary.replace('\n', ' ') if hasattr(entry, 'summary') else 'N/A'
    
    published_parsed = getattr(entry, 'published_parsed', None)
    updated_parsed = getattr(entry, 'updated_parsed', None)
    
    published_date = published_parsed or updated_parsed
    date_str = f"{published_date.tm_year}-{published_date.tm_mon:02d}-{published_date.tm_mday:02d}" if published_date else "N/A"
    
    primary_category = getattr(entry, 'arxiv_primary_category', {}).get('term', 'N/A')
    
    # New fields from documentation (using getattr for safe access)
    comment = getattr(entry, 'arxiv_comment', 'N/A').replace('\n', ' ')
    journal_ref = getattr(entry, 'arxiv_journal_ref', 'N/A').replace('\n', ' ')
    doi = getattr(entry, 'arxiv_doi', 'N/A') # DOI is usually a URL or an ID, keep as is
    
    # Build a list of lines, append only if not 'N/A' to keep output clean
    details_lines = [
        f"Title: {title}",
        f"Authors: {authors}",
        f"arXiv ID: {arxiv_id_match}", # Added arXiv ID
        f"Published Date: {date_str}",
        f"Primary Category: {primary_category}",
        f"Abstract Link: {abstract_link}",
        f"PDF Link: {pdf_link}"
    ]
    
    if comment != 'N/A':
        details_lines.append(f"Comment: {comment}")
    if journal_ref != 'N/A':
        details_lines.append(f"Journal Reference: {journal_ref}")
    if doi != 'N/A':
        details_lines.append(f"DOI: {doi}")

    details_lines.append("\nAbstract:")
    details_lines.append(summary)

    return "\n".join(details_lines)

@mcp.tool()
async def search_papers(
    query: str, max_results: int = 5, sort_by: str = "submittedDate", sort_order: str = "descending"
) -> str:
    """
    General purpose search for academic papers from sources like arXiv. Best for complex queries.
    Args:
        query: Search query using arXiv syntax (e.g., 'ti:"quantum computing" AND au:"John Preskill"').
        max_results: Max number of papers to return.
        sort_by: Sort order ('relevance', 'lastUpdatedDate', 'submittedDate').
        sort_order: Sort direction ('ascending', 'descending').
    """
    params = { "search_query": query, "start": 0, "max_results": max_results, "sortBy": sort_by, "sortOrder": sort_order }
    url = f"{ARXIV_API_BASE}{urllib.parse.urlencode(params)}"
    async with httpx.AsyncClient() as client:
        await asyncio.sleep(3.1) # Added rate limit delay
        response = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=30.0)
    if response.status_code != 200: return f"Error: Academic paper API returned status {response.status_code}" # Generic error message
    feed = feedparser.parse(response.text)
    
    # Check for error entry as per section 3.4 of arXiv API user manual
    if len(feed.entries) == 1 and hasattr(feed.entries[0], 'title') and feed.entries[0].title == 'Error':
        error_summary = getattr(feed.entries[0], 'summary', 'Unknown error').replace('\n', ' ')
        return f"Academic paper API Error: {error_summary}" # Generic error message

    if not feed.entries: return "No papers found for your query."
    formatted_papers = []
    for i, entry in enumerate(feed.entries):
        paper_details = _format_single_paper_details(entry)
        # Find the start of the abstract to truncate for the brief list
        abstract_start_index = paper_details.find("\nAbstract:") # Use the new separator
        if abstract_start_index != -1:
            short_paper_details = paper_details[:abstract_start_index] + f"\nAbstract: {getattr(entry, 'summary', 'N/A').replace('\n', ' ')[:250]}..."
        else:
            short_paper_details = paper_details # Fallback if abstract separator not found
        formatted_papers.append(f"{i+1}. {short_paper_details}")
    return f"Found {len(feed.entries)} papers:\n" + "\n\n---\n\n".join(formatted_papers)

@mcp.tool()
async def find_papers_by_author(author_name: str, max_results: int = 5) -> str:
    """
    Finds recent academic papers by a specific author's name from sources like arXiv.
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
    Retrieves full details for a list of papers using their arXiv IDs from sources like arXiv.
    Args:
        arxiv_ids: A list of arXiv IDs (e.g., ['2307.09288', '1706.03762']).
    """
    id_string = ",".join(arxiv_ids)
    params = {"id_list": id_string, "max_results": len(arxiv_ids)}
    url = f"{ARXIV_API_BASE}{urllib.parse.urlencode(params)}"
    async with httpx.AsyncClient() as client:
        await asyncio.sleep(3.1) # Added rate limit delay
        response = await client.get(url, headers={"User-Agent": USER_AGENT}, timeout=30.0)
    if response.status_code != 200: return f"Error: Academic paper API returned status {response.status_code}" # Generic error message
    feed = feedparser.parse(response.text)
    
    # Check for error entry as per section 3.4 of arXiv API user manual
    if len(feed.entries) == 1 and hasattr(feed.entries[0], 'title') and feed.entries[0].title == 'Error':
        error_summary = getattr(feed.entries[0], 'summary', 'Unknown error').replace('\n', ' ')
        return f"Academic paper API Error: {error_summary}" # Generic error message

    if not feed.entries: return f"Could not find any papers with the provided IDs."
    
    all_details = [_format_single_paper_details(entry) for entry in feed.entries]
    return "\n\n---\n\n".join(all_details)


if __name__ == "__main__":
    mcp.run(transport='stdio')