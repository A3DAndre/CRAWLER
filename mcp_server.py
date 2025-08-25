from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from stores.s3_vector import S3VectorStore

mcp = FastMCP(host="0.0.0.0", stateless_http=True)

def get_store():
    return S3VectorStore(bucket_name="a3wiki", index_name="github")

@mcp.tool()
def search_a3_wiki(query: str):
    store = get_store()
    
    results = store.search(query, limit=5)

    markdown_response = "\n".join([doc.to_md() for doc in results])
    
    return markdown_response

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

@mcp.tool()
def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers together"""
    return a * b

@mcp.tool()
def greet_user(name: str) -> str:
    """Greet a user by name"""
    return f"Hello, {name}! Nice to meet you."

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
