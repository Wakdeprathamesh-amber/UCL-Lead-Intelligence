"""
RAG System Module
Creates vector embeddings and handles semantic search
"""

import os
import sqlite3
import json
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


class LeadRAGSystem:
    """Handles vector embeddings and semantic search for lead conversations"""
    
    def __init__(self, db_path: str = "data/leads.db", chroma_path: str = "data/chroma_db"):
        self.db_path = db_path
        self.chroma_path = chroma_path
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name="lead_conversations")
            print("✅ Loaded existing ChromaDB collection")
        except:
            self.collection = self.chroma_client.create_collection(
                name="lead_conversations",
                metadata={"hnsw:space": "cosine"}
            )
            print("✅ Created new ChromaDB collection")
    
    def create_embeddings(self):
        """Create embeddings for all RAG documents"""
        print("\n🔄 Creating vector embeddings...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all RAG documents
        cursor.execute("""
            SELECT rd.id, rd.lead_id, rd.chunk_type, rd.content, rd.metadata,
                   l.name, l.status
            FROM rag_documents rd
            JOIN leads l ON rd.lead_id = l.lead_id
        """)
        
        documents = cursor.fetchall()
        print(f"   Found {len(documents)} documents to embed")
        
        if len(documents) == 0:
            print("   ⚠️  No documents found!")
            conn.close()
            return
        
        # Check if already embedded
        existing_count = self.collection.count()
        if existing_count >= len(documents):
            print(f"   ✅ Already embedded {existing_count} documents")
            conn.close()
            return
        
        # Prepare batch data
        ids = []
        texts = []
        metadatas = []
        
        for doc_id, lead_id, chunk_type, content, metadata_json, name, status in documents:
            ids.append(f"doc_{doc_id}")
            texts.append(content)
            
            metadata = json.loads(metadata_json) if metadata_json else {}
            metadata.update({
                "doc_id": doc_id,
                "lead_id": lead_id,
                "chunk_type": chunk_type,
                "lead_name": name,
                "status": status
            })
            metadatas.append(metadata)
        
        print(f"   📊 Embedding {len(texts)} documents...")
        
        # Generate embeddings using OpenAI
        try:
            embeddings_list = self.embeddings.embed_documents(texts)
            
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings_list,
                documents=texts,
                metadatas=metadatas
            )
            
            print(f"   ✅ Successfully embedded {len(texts)} documents")
            
        except Exception as e:
            print(f"   ❌ Error creating embeddings: {str(e)}")
            raise
        
        conn.close()
    
    def semantic_search(self, query: str, n_results: int = 5, filter_dict: Dict = None) -> List[Dict]:
        """Perform semantic search on lead conversations"""
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_dict if filter_dict else None
            )
            
            # Format results
            formatted_results = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error in semantic search: {str(e)}")
            return []
    
    def search_by_lead_status(self, query: str, status: str, n_results: int = 5) -> List[Dict]:
        """Search within specific lead status"""
        return self.semantic_search(
            query=query,
            n_results=n_results,
            filter_dict={"status": status}
        )
    
    def search_conversations(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search specifically in conversation summaries"""
        return self.semantic_search(
            query=query,
            n_results=n_results,
            filter_dict={"chunk_type": "conversation_summary"}
        )
    
    def search_objections(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search specifically in objections"""
        return self.semantic_search(
            query=query,
            n_results=n_results,
            filter_dict={"chunk_type": "objections_and_concerns"}
        )
    
    def get_stats(self):
        """Get RAG system statistics"""
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.collection.name
        }


if __name__ == "__main__":
    # Test RAG system
    rag = LeadRAGSystem()
    rag.create_embeddings()
    
    print("\n" + "="*60)
    print("🧪 TESTING SEMANTIC SEARCH")
    print("="*60)
    
    # Test query
    test_query = "students concerned about budget and pricing"
    print(f"\nQuery: '{test_query}'")
    print("-" * 60)
    
    results = rag.semantic_search(test_query, n_results=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n📄 Result {i}:")
        print(f"   Lead: {result['metadata'].get('lead_name', 'Unknown')}")
        print(f"   Status: {result['metadata'].get('status', 'Unknown')}")
        print(f"   Type: {result['metadata'].get('chunk_type', 'Unknown')}")
        print(f"   Distance: {result['distance']:.4f}")
        print(f"   Preview: {result['content'][:200]}...")
    
    print("\n" + "="*60)
    stats = rag.get_stats()
    print(f"✅ RAG System Ready | Documents: {stats['total_documents']}")
    print("="*60)

