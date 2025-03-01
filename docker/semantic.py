from qdrant_client import AsyncQdrantClient, models
from llama_index.embeddings.mistralai import MistralAIEmbedding
from pydantic import BaseModel
import uuid


class CachePiece(BaseModel):
    identifier: str
    question: str
    answer: str
    embeddings: list[float | int]

class AsyncSemanticCache:
    def __init__(self, client: AsyncQdrantClient, embedding_model: MistralAIEmbedding):
        self.client = client
        self.embed_model = embedding_model
        self.collection_name = "semantic_cache"
    async def create_cache_piece(self, question: str, answer: str):
        try:
            identifier = str(uuid.uuid4())
            embeds = self.embed_model.get_text_embedding(text=question)
            self.cache_piece = CachePiece(identifier=identifier, question=question, answer=answer, embeddings=embeds)
        except Exception as e:
            print(f"There was an error: {e}")
            return False
        else:
            return True
    async def update_cache(self):
        try: 
            await self.client.upsert(
                collection_name=self.collection_name, 
                points=[
                    models.PointStruct(
                        id=self.cache_piece.identifier,
                        vector = self.cache_piece.embeddings,
                        payload = self.cache_piece.model_dump(exclude={"embeddings"}),
                    )
                ]
            )
        except Exception as e:
            print(f"There was an error: {e}")
            return False
        else:
            return True
    async def search_cache(self, question: str):
        embeds = await self.embed_model.aget_query_embedding(query=question)
        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=embeds,
            score_threshold=0.8,
            limit = 10
        )
        if len(results) > 0:
            payloads = [hit.payload for hit in results]
            return payloads[0]["answer"]
        else:
            return ""
    