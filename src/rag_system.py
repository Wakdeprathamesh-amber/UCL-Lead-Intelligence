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
    
    def create_embeddings(self, include_events: bool = True, include_raw_text: bool = True):
        """Create embeddings for all RAG documents, timeline events, and raw text fields
        
        Args:
            include_events: Whether to include timeline event documents
            include_raw_text: Whether to include raw communication_timeline and crm_conversation_details
        """
        print("\n🔄 Creating vector embeddings...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all RAG documents (summaries)
        cursor.execute("""
            SELECT rd.id, rd.lead_id, rd.chunk_type, rd.content, rd.metadata,
                   l.name, l.status
            FROM rag_documents rd
            JOIN leads l ON rd.lead_id = l.lead_id
        """)
        
        documents = cursor.fetchall()
        print(f"   Found {len(documents)} summary documents")
        
        # Get timeline events if enabled
        event_documents = []
        if include_events:
            cursor.execute("""
                SELECT rde.id, rde.lead_id, rde.document_type, rde.content, rde.metadata,
                       l.name, l.status
                FROM rag_documents_events rde
                JOIN leads l ON rde.lead_id = l.lead_id
                WHERE rde.content IS NOT NULL AND rde.content != ''
            """)
            event_documents = cursor.fetchall()
            print(f"   Found {len(event_documents)} event documents")
        
        # Get raw communication timeline text if enabled
        raw_timeline_documents = []
        if include_raw_text:
            cursor.execute("""
                SELECT l.lead_id, l.communication_timeline, l.name, l.status
                FROM leads l
                WHERE l.communication_timeline IS NOT NULL 
                  AND l.communication_timeline != ''
                  AND LENGTH(l.communication_timeline) > 100
            """)
            raw_timeline = cursor.fetchall()
            print(f"   Found {len(raw_timeline)} leads with raw communication timeline")
            
            # Chunk large timelines (max 8000 chars per chunk for embedding efficiency)
            max_chunk_size = 8000
            for lead_id, timeline_text, name, status in raw_timeline:
                if timeline_text and len(timeline_text) > max_chunk_size:
                    # Split into chunks
                    chunks = [timeline_text[i:i+max_chunk_size] 
                             for i in range(0, len(timeline_text), max_chunk_size)]
                    for chunk_idx, chunk in enumerate(chunks):
                        raw_timeline_documents.append((
                            f"{lead_id}_timeline_chunk_{chunk_idx}",
                            lead_id,
                            "raw_communication_timeline",
                            chunk,
                            name,
                            status
                        ))
                elif timeline_text:
                    raw_timeline_documents.append((
                        f"{lead_id}_timeline",
                        lead_id,
                        "raw_communication_timeline",
                        timeline_text,
                        name,
                        status
                    ))
            print(f"   Created {len(raw_timeline_documents)} raw timeline chunks")
        
        # Get raw CRM conversation details if enabled
        raw_crm_documents = []
        if include_raw_text:
            cursor.execute("""
                SELECT l.lead_id, l.crm_conversation_details, l.name, l.status
                FROM leads l
                WHERE l.crm_conversation_details IS NOT NULL 
                  AND l.crm_conversation_details != ''
                  AND LENGTH(l.crm_conversation_details) > 50
            """)
            raw_crm = cursor.fetchall()
            print(f"   Found {len(raw_crm)} leads with raw CRM conversation details")
            
            # Chunk large CRM details (max 8000 chars per chunk)
            max_chunk_size = 8000
            for lead_id, crm_text, name, status in raw_crm:
                if crm_text and len(crm_text) > max_chunk_size:
                    # Split into chunks
                    chunks = [crm_text[i:i+max_chunk_size] 
                             for i in range(0, len(crm_text), max_chunk_size)]
                    for chunk_idx, chunk in enumerate(chunks):
                        raw_crm_documents.append((
                            f"{lead_id}_crm_chunk_{chunk_idx}",
                            lead_id,
                            "raw_crm_conversation_details",
                            chunk,
                            name,
                            status
                        ))
                elif crm_text:
                    raw_crm_documents.append((
                        f"{lead_id}_crm",
                        lead_id,
                        "raw_crm_conversation_details",
                        crm_text,
                        name,
                        status
                    ))
            print(f"   Created {len(raw_crm_documents)} raw CRM chunks")
        
        # Get tasks if enabled
        task_documents = []
        if include_events:  # Use same flag as events
            cursor.execute("""
                SELECT lt.id, lt.lead_id, lt.description, lt.task_type, lt.status,
                       lt.due_date, l.name, l.status as lead_status
                FROM lead_tasks lt
                JOIN leads l ON lt.lead_id = l.lead_id
                WHERE lt.description IS NOT NULL 
                  AND lt.description != ''
                  AND LENGTH(lt.description) > 10
            """)
            tasks = cursor.fetchall()
            print(f"   Found {len(tasks)} tasks to embed")
            
            for task_id, lead_id, description, task_type, task_status, due_date, name, lead_status in tasks:
                # Create task document with context
                task_text = f"Task: {description}"
                if task_type:
                    task_text += f" | Type: {task_type}"
                if task_status:
                    task_text += f" | Status: {task_status}"
                if due_date:
                    task_text += f" | Due: {due_date}"
                
                task_documents.append((
                    f"task_{task_id}",
                    lead_id,
                    "task",
                    task_text,
                    name,
                    lead_status,
                    task_status or "pending"
                ))
            print(f"   Created {len(task_documents)} task documents")
        
        # Combine all document types
        all_documents = documents + event_documents
        total_expected = len(all_documents) + len(raw_timeline_documents) + len(raw_crm_documents) + len(task_documents)
        
        if total_expected == 0:
            print("   ⚠️  No documents found!")
            conn.close()
            return
        
        # Check if already embedded
        # If including raw text, check if we need to add it
        existing_count = self.collection.count()
        
        if include_raw_text:
            # Check if raw text sources exist and are already embedded
            # We'll proceed if embeddings are significantly less than expected
            if existing_count < total_expected * 0.8:
                print(f"   ℹ️  Current embeddings: {existing_count}, Expected with raw text: {total_expected}")
                print(f"   ℹ️  Will add raw timeline ({len(raw_timeline_documents)} chunks) and CRM ({len(raw_crm_documents)} chunks)")
            elif existing_count >= total_expected * 0.9:
                print(f"   ✅ Already embedded {existing_count} documents (approx {total_expected} expected)")
                conn.close()
                return
        else:
            # If not including raw text, use original logic
            if existing_count >= len(all_documents) * 0.9:  # Allow 10% variance
                print(f"   ✅ Already embedded {existing_count} documents (approx {len(all_documents)} expected)")
            conn.close()
            return
        
        # Prepare batch data
        ids = []
        texts = []
        metadatas = []
        
        # Process summary documents
        for doc_id, lead_id, chunk_type, content, metadata_json, name, status in documents:
            ids.append(f"doc_{doc_id}")
            texts.append(content)
            
            metadata = json.loads(metadata_json) if metadata_json else {}
            metadata.update({
                "doc_id": str(doc_id) if doc_id else "",
                "lead_id": str(lead_id) if lead_id else "",
                "chunk_type": str(chunk_type) if chunk_type else "",
                "lead_name": str(name) if name else "Unknown",
                "status": str(status) if status else "Unknown",
                "source": "summary"
            })
            # Remove None values (ChromaDB doesn't accept None)
            metadata = {k: v for k, v in metadata.items() if v is not None}
            metadatas.append(metadata)
        
        # Process event documents
        for doc_id, lead_id, doc_type, content, metadata_json, name, status in event_documents:
            ids.append(f"event_{doc_id}")
            texts.append(content)
            
            metadata = json.loads(metadata_json) if metadata_json else {}
            metadata.update({
                "doc_id": str(doc_id) if doc_id else "",
                "lead_id": str(lead_id) if lead_id else "",
                "chunk_type": str(doc_type) if doc_type else "",
                "lead_name": str(name) if name else "Unknown",
                "status": str(status) if status else "Unknown",
                "source": "event"
            })
            # Remove None values (ChromaDB doesn't accept None)
            metadata = {k: v for k, v in metadata.items() if v is not None}
            metadatas.append(metadata)
        
        # Process raw timeline documents
        for chunk_id, lead_id, chunk_type, content, name, status in raw_timeline_documents:
            ids.append(f"raw_timeline_{chunk_id}")
            texts.append(content)
            
            metadata = {
                "chunk_id": str(chunk_id),
                "lead_id": str(lead_id) if lead_id else "",
                "chunk_type": str(chunk_type) if chunk_type else "",
                "lead_name": str(name) if name else "Unknown",
                "status": str(status) if status else "Unknown",
                "source": "raw_timeline"
            }
            # Remove None values
            metadata = {k: v for k, v in metadata.items() if v is not None}
            metadatas.append(metadata)
        
        # Process raw CRM documents
        for chunk_id, lead_id, chunk_type, content, name, status in raw_crm_documents:
            ids.append(f"raw_crm_{chunk_id}")
            texts.append(content)
            
            metadata = {
                "chunk_id": str(chunk_id),
                "lead_id": str(lead_id) if lead_id else "",
                "chunk_type": str(chunk_type) if chunk_type else "",
                "lead_name": str(name) if name else "Unknown",
                "status": str(status) if status else "Unknown",
                "source": "raw_crm"
            }
            # Remove None values
            metadata = {k: v for k, v in metadata.items() if v is not None}
            metadatas.append(metadata)
        
        # Process task documents
        for chunk_id, lead_id, chunk_type, content, name, status, task_status in task_documents:
            ids.append(f"task_{chunk_id}")
            texts.append(content)
            
            metadata = {
                "chunk_id": str(chunk_id),
                "lead_id": str(lead_id) if lead_id else "",
                "chunk_type": str(chunk_type) if chunk_type else "",
                "lead_name": str(name) if name else "Unknown",
                "status": str(status) if status else "Unknown",
                "task_status": str(task_status) if task_status else "pending",
                "source": "task"
            }
            # Remove None values
            metadata = {k: v for k, v in metadata.items() if v is not None}
            metadatas.append(metadata)
        
        print(f"   📊 Embedding {len(texts)} documents (in batches)...")
        print(f"      - {len(documents)} summaries")
        print(f"      - {len(event_documents)} events")
        print(f"      - {len(raw_timeline_documents)} raw timeline chunks")
        print(f"      - {len(raw_crm_documents)} raw CRM chunks")
        print(f"      - {len(task_documents)} tasks")
        
        # Generate embeddings in batches (to avoid API limits)
        batch_size = 100
        total_embedded = 0
        
        try:
            for i in range(0, len(texts), batch_size):
                batch_ids = ids[i:i+batch_size]
                batch_texts = texts[i:i+batch_size]
                batch_metadatas = metadatas[i:i+batch_size]
                
                print(f"   📦 Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}...")
                
                embeddings_list = self.embeddings.embed_documents(batch_texts)
                
                # Check for existing IDs and update instead of add
                existing_ids = set()
                try:
                    # Get existing IDs in this batch
                    existing = self.collection.get(ids=batch_ids)
                    if existing and existing.get('ids'):
                        existing_ids = set(existing['ids'])
                except:
                    # IDs don't exist, proceed with add
                    pass
                
                # Separate new and existing
                new_ids = []
                new_embeddings = []
                new_documents = []
                new_metadatas = []
                
                update_ids = []
                update_embeddings = []
                update_documents = []
                update_metadatas = []
                
                for idx, doc_id in enumerate(batch_ids):
                    if doc_id in existing_ids:
                        update_ids.append(doc_id)
                        update_embeddings.append(embeddings_list[idx])
                        update_documents.append(batch_texts[idx])
                        update_metadatas.append(batch_metadatas[idx])
                    else:
                        new_ids.append(doc_id)
                        new_embeddings.append(embeddings_list[idx])
                        new_documents.append(batch_texts[idx])
                        new_metadatas.append(batch_metadatas[idx])
                
                # Add new documents
                if new_ids:
                    self.collection.add(
                        ids=new_ids,
                        embeddings=new_embeddings,
                        documents=new_documents,
                        metadatas=new_metadatas
                    )
                
                # Update existing documents
                if update_ids:
                    self.collection.update(
                        ids=update_ids,
                        embeddings=update_embeddings,
                        documents=update_documents,
                        metadatas=update_metadatas
                    )
                
                total_embedded += len(batch_texts)
                print(f"   ✅ Embedded {total_embedded}/{len(texts)} documents")
            
            print(f"   ✅ Successfully embedded {total_embedded} documents")
            
        except Exception as e:
            print(f"   ❌ Error creating embeddings: {str(e)}")
            raise
        
        conn.close()
    
    def semantic_search(self, query: str, n_results: int = 5, filter_dict: Dict = None) -> List[Dict]:
        """Perform semantic search on lead conversations with error handling"""
        if not query or not isinstance(query, str) or len(query.strip()) == 0:
            return []
        
        if n_results < 1 or n_results > 100:
            n_results = min(max(1, n_results), 100)  # Clamp between 1 and 100
        
        try:
            # Validate API key
            if not os.getenv("OPENAI_API_KEY"):
                print("⚠️  OpenAI API key not configured. Semantic search unavailable.")
                return []
            
            # Generate query embedding with retry
            max_retries = 3
            query_embedding = None
            for attempt in range(max_retries):
                try:
                    query_embedding = self.embeddings.embed_query(query)
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(1 * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        raise
            
            if not query_embedding:
                return []
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_dict if filter_dict else None
            )
            
            # Format results
            formatted_results = []
            if results and results.get('documents') and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                        'distance': results['distances'][0][i] if results.get('distances') else None
                    })
            
            return formatted_results
            
        except Exception as e:
            error_msg = str(e).lower()
            if "rate limit" in error_msg or "429" in error_msg:
                print("⚠️  API rate limit exceeded. Please wait a moment and try again.")
            elif "authentication" in error_msg or "401" in error_msg:
                print("⚠️  API authentication failed. Please check your API key.")
            else:
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

