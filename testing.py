
from stores.s3_vector import S3VectorStore

from utils.logger import setup_logger
logger = setup_logger(__name__)


def get_store():
    return S3VectorStore(bucket_name="a3wiki", index_name="github2")



if __name__ == "__main__":
    
    query = "Buora Framework"
    logger.info(f"Searching A3 Data Wiki for query: {query}")
    store = get_store()
    logger.info("Vector store initialized")
    results = store.search(query, limit=5)
    markdown_response = "\n".join([doc.to_md() for doc in results])
    print(markdown_response)
    logger.info(f"Search completed with {len(results)} results found")
    
