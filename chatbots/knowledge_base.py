import os
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import hashlib

from langchain.schema import Document


class FootballKnowledgeManager:
    """Manages football knowledge documents for the RAG system"""
    
    def __init__(self, knowledge_path: str = "data/football_knowledge"):
        self.knowledge_path = Path(knowledge_path)
        self.knowledge_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize knowledge categories
        self.categories = {
            "teams": "Team information, statistics, and profiles",
            "players": "Player data, performance metrics, and transfers",
            "matches": "Match results, statistics, and analysis",
            "leagues": "League information, standings, and rules",
            "betting": "Betting strategies, tips, and market analysis",
            "statistics": "Historical data and statistical analysis"
        }
        
        # Create category directories
        for category in self.categories.keys():
            (self.knowledge_path / category).mkdir(exist_ok=True)
    
    def add_document(self, content: str, title: str, category: str, 
                    source: str = "manual", metadata: Dict = None) -> str:
        """Add a document to the knowledge base"""
        
        if category not in self.categories:
            raise ValueError(f"Invalid category. Must be one of: {list(self.categories.keys())}")
        
        # Generate document ID
        doc_id = self._generate_doc_id(title, content)
        
        # Prepare metadata
        doc_metadata = {
            "id": doc_id,
            "title": title,
            "category": category,
            "source": source,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "content_hash": hashlib.md5(content.encode()).hexdigest(),
            **(metadata or {})
        }
        
        # Create document
        document = {
            "content": content,
            "metadata": doc_metadata
        }
        
        # Save to file
        doc_path = self.knowledge_path / category / f"{doc_id}.json"
        with open(doc_path, 'w', encoding='utf-8') as f:
            json.dump(document, f, indent=2, ensure_ascii=False)
        
        return doc_id
    
    def _generate_doc_id(self, title: str, content: str) -> str:
        """Generate a unique document ID"""
        combined = f"{title}_{content[:100]}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    def get_document(self, doc_id: str, category: str = None) -> Optional[Document]:
        """Retrieve a document by ID"""
        if category:
            doc_path = self.knowledge_path / category / f"{doc_id}.json"
            if doc_path.exists():
                with open(doc_path, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    return Document(
                        page_content=doc_data["content"],
                        metadata=doc_data["metadata"]
                    )
        else:
            # Search all categories
            for cat in self.categories.keys():
                doc_path = self.knowledge_path / cat / f"{doc_id}.json"
                if doc_path.exists():
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        doc_data = json.load(f)
                        return Document(
                            page_content=doc_data["content"],
                            metadata=doc_data["metadata"]
                        )
        
        return None
    
    def get_all_documents(self, category: str = None) -> List[Document]:
        """Get all documents or documents from a specific category"""
        documents = []
        
        categories_to_check = [category] if category else self.categories.keys()
        
        for cat in categories_to_check:
            cat_path = self.knowledge_path / cat
            if cat_path.exists():
                for doc_file in cat_path.glob("*.json"):
                    try:
                        with open(doc_file, 'r', encoding='utf-8') as f:
                            doc_data = json.load(f)
                            documents.append(Document(
                                page_content=doc_data["content"],
                                metadata=doc_data["metadata"]
                            ))
                    except Exception as e:
                        print(f"Error loading document {doc_file}: {e}")
        
        return documents
    
    def update_document(self, doc_id: str, content: str = None, 
                       metadata: Dict = None, category: str = None) -> bool:
        """Update an existing document"""
        
        # Find the document
        existing_doc = self.get_document(doc_id, category)
        if not existing_doc:
            return False
        
        # Get current category from metadata
        current_category = existing_doc.metadata.get("category")
        if not current_category:
            return False
        
        # Update content and metadata
        new_content = content if content is not None else existing_doc.page_content
        new_metadata = existing_doc.metadata.copy()
        
        if metadata:
            new_metadata.update(metadata)
        
        new_metadata["updated_at"] = datetime.now().isoformat()
        new_metadata["content_hash"] = hashlib.md5(new_content.encode()).hexdigest()
        
        # Save updated document
        doc_path = self.knowledge_path / current_category / f"{doc_id}.json"
        document = {
            "content": new_content,
            "metadata": new_metadata
        }
        
        try:
            with open(doc_path, 'w', encoding='utf-8') as f:
                json.dump(document, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False
    
    def delete_document(self, doc_id: str, category: str = None) -> bool:
        """Delete a document"""
        if category:
            doc_path = self.knowledge_path / category / f"{doc_id}.json"
            if doc_path.exists():
                doc_path.unlink()
                return True
        else:
            # Search all categories
            for cat in self.categories.keys():
                doc_path = self.knowledge_path / cat / f"{doc_id}.json"
                if doc_path.exists():
                    doc_path.unlink()
                    return True
        
        return False
    
    def search_documents(self, query: str, category: str = None, 
                        limit: int = 10) -> List[Document]:
        """Simple text search in documents"""
        documents = self.get_all_documents(category)
        query_lower = query.lower()
        
        matching_docs = []
        for doc in documents:
            content_lower = doc.page_content.lower()
            title_lower = doc.metadata.get("title", "").lower()
            
            if query_lower in content_lower or query_lower in title_lower:
                matching_docs.append(doc)
        
        return matching_docs[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        stats = {
            "total_documents": 0,
            "categories": {},
            "last_updated": None
        }
        
        latest_update = None
        
        for category in self.categories.keys():
            cat_path = self.knowledge_path / category
            if cat_path.exists():
                doc_files = list(cat_path.glob("*.json"))
                stats["categories"][category] = len(doc_files)
                stats["total_documents"] += len(doc_files)
                
                # Check for latest update
                for doc_file in doc_files:
                    try:
                        with open(doc_file, 'r', encoding='utf-8') as f:
                            doc_data = json.load(f)
                            updated_at = doc_data["metadata"].get("updated_at")
                            if updated_at:
                                if latest_update is None or updated_at > latest_update:
                                    latest_update = updated_at
                    except:
                        continue
        
        stats["last_updated"] = latest_update
        return stats
    
    def create_sample_knowledge(self):
        """Create sample football knowledge for testing"""
        
        # Sample team data
        team_docs = [
            {
                "title": "Liverpool FC Profile",
                "category": "teams",
                "content": """Liverpool Football Club is an English professional football club based in Liverpool. 
                Founded in 1892, Liverpool has won 19 league titles, 8 FA Cups, 9 League Cups, 15 FA Community Shields, 
                6 European Cups/Champions League titles, 3 UEFA Cups/Europa League titles, 4 UEFA Super Cups, and 1 FIFA Club World Cup.
                
                Recent Performance:
                - Premier League Champions 2019-20
                - Champions League Winners 2018-19
                - Key Players: Mohamed Salah, Virgil van Dijk, Sadio Mané
                - Manager: Jürgen Klopp (known for high-intensity pressing style)
                - Home Stadium: Anfield (capacity: 53,394)
                
                Playing Style: Known for gegenpressing, fast transitions, and attacking full-backs.
                Strengths: Strong mentality, excellent in big games, solid defense with van Dijk.
                Weaknesses: Can struggle against deep defensive blocks, injury-prone squad depth."""
            },
            {
                "title": "Manchester City Profile",
                "category": "teams", 
                "content": """Manchester City is an English football club based in Manchester.
                Under Pep Guardiola, City has become one of the most dominant teams in world football.
                
                Recent Performance:
                - Premier League Champions 2020-21, 2021-22, 2022-23
                - Champions League Winners 2022-23
                - Key Players: Kevin De Bruyne, Erling Haaland, Rodri
                - Manager: Pep Guardiola (possession-based philosophy)
                - Home Stadium: Etihad Stadium (capacity: 55,017)
                
                Playing Style: Possession-based football, positional play, high defensive line.
                Strengths: Technical quality, squad depth, tactical flexibility.
                Weaknesses: Can be vulnerable to counter-attacks, high defensive line exposed."""
            }
        ]
        
        # Sample betting strategies
        betting_docs = [
            {
                "title": "Value Betting Strategy",
                "category": "betting",
                "content": """Value betting is the practice of betting when the probability of an outcome is greater 
                than the probability implied by the bookmaker's odds.
                
                Key Principles:
                1. Calculate true probability of outcomes
                2. Compare with bookmaker's implied probability
                3. Bet when you find positive expected value
                4. Use proper bankroll management
                
                Example: If you calculate Liverpool has 60% chance to win, but odds imply 50% (2.00 odds), 
                this represents value.
                
                Risk Management:
                - Never bet more than 2-5% of bankroll on single bet
                - Track all bets and results
                - Focus on long-term profitability
                - Avoid emotional betting"""
            },
            {
                "title": "Team Form Analysis",
                "category": "betting",
                "content": """Analyzing team form is crucial for successful football betting.
                
                Key Metrics to Track:
                1. Recent Results (last 5-10 games)
                2. Goals scored and conceded
                3. Home vs Away performance
                4. Head-to-head records
                5. Injury list and suspensions
                6. Player morale and manager pressure
                
                Advanced Metrics:
                - Expected Goals (xG) vs actual goals
                - Shot conversion rates
                - Defensive actions per game
                - Possession statistics
                
                Red Flags:
                - Multiple key player injuries
                - Recent manager changes
                - Poor away form for traveling team
                - Midweek European fixtures causing fatigue"""
            }
        ]
        
        # Sample match analysis
        match_docs = [
            {
                "title": "Liverpool vs Manchester City Head-to-Head",
                "category": "matches",
                "content": """Historical analysis of Liverpool vs Manchester City fixtures.
                
                Recent Meetings (Last 10):
                - Liverpool wins: 4
                - Manchester City wins: 4  
                - Draws: 2
                - Average goals per game: 2.8
                
                Key Trends:
                - High-scoring fixtures (Over 2.5 goals in 70% of meetings)
                - Both teams to score in 80% of recent meetings
                - City stronger at Etihad, Liverpool stronger at Anfield
                - Tactical battle between Klopp's pressing and Guardiola's possession
                
                Betting Insights:
                - Over 2.5 goals is often good value
                - Both teams to score is reliable
                - Home advantage is significant in this fixture
                - Early goals often lead to open, attacking games"""
            }
        ]
        
        # Add all sample documents
        for doc_data in team_docs + betting_docs + match_docs:
            self.add_document(
                content=doc_data["content"],
                title=doc_data["title"],
                category=doc_data["category"],
                source="sample_data"
            )
        
        print(f"Created {len(team_docs + betting_docs + match_docs)} sample documents")


def create_knowledge_manager() -> FootballKnowledgeManager:
    """Factory function to create a FootballKnowledgeManager instance"""
    return FootballKnowledgeManager()


# Singleton instance
_knowledge_manager = None

def get_knowledge_manager() -> FootballKnowledgeManager:
    """Get the singleton knowledge manager instance"""
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = create_knowledge_manager()
    return _knowledge_manager