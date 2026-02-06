"""
VECTOR MEMORY CONFIGURATION
Long-term semantic memory for AI agents
"""
import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

class VectorMemory:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        self.index_name = 'tree-of-life-memory'
        
    def create_index(self):
        """Create vector index for semantic search"""
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # OpenAI embedding dimension
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region=os.getenv('PINECONE_ENVIRONMENT', 'us-west-2')
                )
            )
            print(f"✅ Vector index '{self.index_name}' created")
        else:
            print(f"✓ Vector index '{self.index_name}' already exists")
            
    def get_index(self):
        return self.pc.Index(self.index_name)
