from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
import asyncio


qc = AsyncQdrantClient("http://localhost:6333")

async def main():
    try:
        res = await qc.create_collection(
            collection_name="semantic_cache",
            vectors_config=models.VectorParams(
            size=1024,  # Vector size is defined by used model
            distance=models.Distance.COSINE,
            ),
        )
        return res
    except Exception as e:
        if isinstance(e, UnexpectedResponse):
            if e.status_code == 409:
                print("The collection already exist, skipping creation...")
                return False
            else:
                print(f"There was an unexpected response with status code {e.status_code}: {e}")
                return False
        else:
            print(f"There was an error: {e}")
            return False
                    

if __name__ == "__main__":
    asyncio.run(main())
