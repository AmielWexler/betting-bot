import os
import pickle
from typing import List, Dict, Optional, Any
import numpy as np
from pathlib import Path
import json
from datetime import datetime

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.retrievers import BM25Retriever, EnsembleRetriever


class FootballRAGSystem:
    """RAG system for football betting knowledge using FAISS vector store"""
    
    def __init__(self, vector_store_path: str = "data/vector_store", model_name: str = "all-MiniLM-L6-v2"):
        self.vector_store_path = Path(vector_store_path)
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        self.vector_store: Optional[FAISS] = None
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.ensemble_retriever: Optional[EnsembleRetriever] = None
        
        # User-specific vector stores for personalized data
        self.user_stores: Dict[str, FAISS] = {}
        self.user_stores_path = self.vector_store_path / "user_stores"
        self.user_stores_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing vector store if available
        self._load_vector_store()
        self._load_user_stores()
    
    def _load_vector_store(self) -> bool:
        """Load existing FAISS vector store from disk"""
        try:
            faiss_path = self.vector_store_path / "faiss_index"
            if faiss_path.exists():
                self.vector_store = FAISS.load_local(
                    str(faiss_path), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                
                # Load BM25 retriever if available
                bm25_path = self.vector_store_path / "bm25_retriever.pkl"
                if bm25_path.exists():
                    with open(bm25_path, 'rb') as f:
                        self.bm25_retriever = pickle.load(f)
                    
                    # Create ensemble retriever
                    self._create_ensemble_retriever()
                
                print(f"Loaded vector store with {self.vector_store.index.ntotal} documents")
                return True
        except Exception as e:
            print(f"Error loading vector store: {e}")
        
        return False
    
    def _save_vector_store(self):
        """Save FAISS vector store to disk"""
        try:
            if self.vector_store:
                faiss_path = self.vector_store_path / "faiss_index"
                self.vector_store.save_local(str(faiss_path))
                
                # Save BM25 retriever
                if self.bm25_retriever:
                    bm25_path = self.vector_store_path / "bm25_retriever.pkl"
                    with open(bm25_path, 'wb') as f:
                        pickle.dump(self.bm25_retriever, f)
                
                print("Vector store saved successfully")
        except Exception as e:
            print(f"Error saving vector store: {e}")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store"""
        if not documents:
            return []
        
        # Split documents into chunks
        chunked_docs = []
        for doc in documents:
            chunks = self.text_splitter.split_documents([doc])
            chunked_docs.extend(chunks)
        
        if not chunked_docs:
            return []
        
        # Create or update vector store
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(chunked_docs, self.embeddings)
        else:
            self.vector_store.add_documents(chunked_docs)
        
        # Create/update BM25 retriever
        all_docs = self._get_all_documents()
        self.bm25_retriever = BM25Retriever.from_documents(all_docs)
        self.bm25_retriever.k = 5
        
        # Create ensemble retriever
        self._create_ensemble_retriever()
        
        # Save to disk
        self._save_vector_store()
        
        return [chunk.metadata.get('id', str(i)) for i, chunk in enumerate(chunked_docs)]
    
    def _get_all_documents(self) -> List[Document]:
        """Get all documents from the vector store"""
        if not self.vector_store:
            return []
        
        # This is a simplified approach - in production you might want to store docs separately
        try:
            # Get all document IDs and retrieve documents
            all_docs = []
            for i in range(self.vector_store.index.ntotal):
                doc_dict = self.vector_store.docstore.search(str(i))
                if doc_dict:
                    all_docs.append(Document(
                        page_content=doc_dict.page_content,
                        metadata=doc_dict.metadata
                    ))
            return all_docs
        except:
            # Fallback: return empty list if we can't retrieve all docs
            return []
    
    def _create_ensemble_retriever(self):
        """Create ensemble retriever combining FAISS and BM25"""
        if self.vector_store and self.bm25_retriever:
            faiss_retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
            
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[faiss_retriever, self.bm25_retriever],
                weights=[0.7, 0.3]  # Favor vector search slightly over BM25
            )
    
    def retrieve_relevant_documents(self, query: str, k: int = 5, 
                                  score_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query"""
        if not self.vector_store:
            return []
        
        try:
            # Use ensemble retriever if available, otherwise use vector store
            if self.ensemble_retriever:
                docs = self.ensemble_retriever.get_relevant_documents(query)
            else:
                docs = self.vector_store.similarity_search(query, k=k)
            
            # Format results
            results = []
            for doc in docs[:k]:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "unknown"),
                    "category": doc.metadata.get("category", "general")
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """Get documents with similarity scores"""
        if not self.vector_store:
            return []
        
        try:
            return self.vector_store.similarity_search_with_score(query, k=k)
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if not self.vector_store:
            return {"total_documents": 0, "status": "not_initialized"}
        
        return {
            "total_documents": self.vector_store.index.ntotal,
            "embedding_dimension": self.vector_store.index.d,
            "status": "ready",
            "has_bm25": self.bm25_retriever is not None,
            "has_ensemble": self.ensemble_retriever is not None
        }
    
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """Delete documents by IDs (limited support in FAISS)"""
        # Note: FAISS doesn't support easy deletion of specific documents
        # This would require rebuilding the index
        print("Document deletion not fully supported with FAISS. Consider rebuilding the index.")
        return False
    
    def update_document(self, doc_id: str, new_document: Document) -> bool:
        """Update a document (requires rebuilding for FAISS)"""
        print("Document updates not fully supported with FAISS. Consider rebuilding the index.")
        return False
    
    def clear_store(self):
        """Clear the entire vector store"""
        self.vector_store = None
        self.bm25_retriever = None
        self.ensemble_retriever = None
        
        # Remove files
        try:
            import shutil
            if self.vector_store_path.exists():
                shutil.rmtree(self.vector_store_path)
                self.vector_store_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error clearing store: {e}")
    
    def _load_user_stores(self):
        """Load existing user-specific vector stores"""
        try:
            for user_dir in self.user_stores_path.glob("user_*"):
                if user_dir.is_dir():
                    user_id = user_dir.name.replace("user_", "")
                    faiss_path = user_dir / "faiss_index"
                    if faiss_path.exists():
                        user_store = FAISS.load_local(
                            str(faiss_path),
                            self.embeddings,
                            allow_dangerous_deserialization=True
                        )
                        self.user_stores[user_id] = user_store
                        print(f"Loaded user store for user {user_id}")
        except Exception as e:
            print(f"Error loading user stores: {e}")
    
    def _save_user_store(self, user_id: str):
        """Save user-specific vector store to disk"""
        try:
            if user_id in self.user_stores:
                user_dir = self.user_stores_path / f"user_{user_id}"
                user_dir.mkdir(exist_ok=True)
                faiss_path = user_dir / "faiss_index"
                self.user_stores[user_id].save_local(str(faiss_path))
                print(f"Saved user store for user {user_id}")
        except Exception as e:
            print(f"Error saving user store for user {user_id}: {e}")
    
    def add_user_document(self, user_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """Add a document to user-specific vector store"""
        try:
            if metadata is None:
                metadata = {}
            
            metadata.update({
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "type": "user_data"
            })
            
            doc = Document(page_content=content, metadata=metadata)
            chunks = self.text_splitter.split_documents([doc])
            
            if not chunks:
                return False
            
            # Create or update user store
            if user_id not in self.user_stores:
                self.user_stores[user_id] = FAISS.from_documents(chunks, self.embeddings)
            else:
                self.user_stores[user_id].add_documents(chunks)
            
            # Save to disk
            self._save_user_store(user_id)
            return True
            
        except Exception as e:
            print(f"Error adding user document for user {user_id}: {e}")
            return False
    
    def store_user_betting_analysis(self, user_id: str, analysis: str, 
                                  match_info: Dict[str, Any] = None) -> bool:
        """Store user's betting analysis for future reference"""
        try:
            metadata = {
                "category": "betting_analysis",
                "match_info": match_info or {},
                "analysis_type": "user_generated"
            }
            
            content = f"User Betting Analysis:\n{analysis}"
            if match_info:
                content += f"\nMatch Context: {json.dumps(match_info, indent=2)}"
            
            return self.add_user_document(user_id, content, metadata)
            
        except Exception as e:
            print(f"Error storing betting analysis for user {user_id}: {e}")
            return False
    
    def store_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Store user betting preferences and settings"""
        try:
            metadata = {
                "category": "user_preferences",
                "preferences_type": "betting_settings"
            }
            
            content = f"User Preferences:\n{json.dumps(preferences, indent=2)}"
            return self.add_user_document(user_id, content, metadata)
            
        except Exception as e:
            print(f"Error storing preferences for user {user_id}: {e}")
            return False
    
    def store_user_bet_history(self, user_id: str, bet_data: Dict[str, Any]) -> bool:
        """Store user's betting history for pattern analysis"""
        try:
            metadata = {
                "category": "bet_history",
                "bet_outcome": bet_data.get("outcome", "pending"),
                "bet_type": bet_data.get("type", "unknown")
            }
            
            content = f"Bet Record:\n{json.dumps(bet_data, indent=2)}"
            return self.add_user_document(user_id, content, metadata)
            
        except Exception as e:
            print(f"Error storing bet history for user {user_id}: {e}")
            return False
    
    def retrieve_user_context(self, user_id: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve user-specific context for personalized responses"""
        if user_id not in self.user_stores:
            return []
        
        try:
            user_store = self.user_stores[user_id]
            docs = user_store.similarity_search(query, k=k)
            
            results = []
            for doc in docs:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": f"user_{user_id}_data",
                    "category": doc.metadata.get("category", "user_data")
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error retrieving user context for user {user_id}: {e}")
            return []
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user-specific data"""
        if user_id not in self.user_stores:
            return {"total_documents": 0, "status": "no_data"}
        
        try:
            user_store = self.user_stores[user_id]
            return {
                "total_documents": user_store.index.ntotal,
                "user_id": user_id,
                "status": "active"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def clear_user_data(self, user_id: str) -> bool:
        """Clear all data for a specific user"""
        try:
            if user_id in self.user_stores:
                del self.user_stores[user_id]
            
            # Remove user directory
            user_dir = self.user_stores_path / f"user_{user_id}"
            if user_dir.exists():
                import shutil
                shutil.rmtree(user_dir)
            
            return True
            
        except Exception as e:
            print(f"Error clearing user data for user {user_id}: {e}")
            return False


def create_football_rag_system() -> FootballRAGSystem:
    """Factory function to create a FootballRAGSystem instance"""
    return FootballRAGSystem()


# Singleton instance
_rag_system = None

def get_rag_system() -> FootballRAGSystem:
    """Get the singleton RAG system instance"""
    global _rag_system
    if _rag_system is None:
        _rag_system = create_football_rag_system()
    return _rag_system