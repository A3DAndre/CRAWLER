import io
import json
import sys
from typing import Callable
from dotenv import load_dotenv
load_dotenv()
from stores.s3_vector import S3VectorStore

def main():
    store = S3VectorStore(bucket_name="test-bucket", index_name="test-index")
    try:
        result = store.health_check()
        print(f"health_check returned: {result}")
    except Exception as e:
        print(f"health_check raised exception: {e}")


if __name__ == "__main__":
    main()
