from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from stores.s3_vector import S3VectorStore

from utils.logger import setup_logger

logger = setup_logger(__name__)

mcp = FastMCP(host="0.0.0.0", stateless_http=True)

@mcp.tool()
def search_a3_wiki(query: str):
    """Search A3 Data Wiki for relevant information"""
    logger.info(f"Searching A3 Data Wiki for query: {query}")
    store = S3VectorStore(bucket_name="a3wiki", index_name="github2")
    logger.info("Vector store initialized")
    results = store.search(query, limit=5)

    markdown_response = "\n".join([doc.to_md() for doc in results])

    logger.info(f"Search completed with {len(results)} results found")
    return markdown_response


@mcp.tool()
def greet_user(name: str) -> str:
    """Greet a user by name"""
    return f"Hello, {name}! Nice to meet you."

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
