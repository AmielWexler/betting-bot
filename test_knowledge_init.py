#!/usr/bin/env python3
"""
Test script to initialize and verify the knowledge base and RAG system
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_knowledge_initialization():
    """Test knowledge base and RAG system initialization"""
    print("🧪 Testing Knowledge Base and RAG System Initialization...")
    
    try:
        # Import our components
        from chatbots.knowledge_base import get_knowledge_manager
        from chatbots.rag_system import get_rag_system
        from chatbots.betting_bot import get_betting_chatbot
        
        print("✅ Successfully imported all components")
        
        # Test knowledge manager
        print("\n📚 Testing Knowledge Manager...")
        knowledge_manager = get_knowledge_manager()
        
        # Check if knowledge base is empty and create sample data
        stats = knowledge_manager.get_statistics()
        print(f"Current knowledge base stats: {stats}")
        
        if stats["total_documents"] == 0:
            print("📝 Creating sample knowledge...")
            knowledge_manager.create_sample_knowledge()
            stats = knowledge_manager.get_statistics()
            print(f"After creation: {stats}")
        
        # Test RAG system
        print("\n🔍 Testing RAG System...")
        rag_system = get_rag_system()
        rag_stats = rag_system.get_stats()
        print(f"RAG system stats: {rag_stats}")
        
        # Load documents into RAG if needed
        if rag_stats["total_documents"] == 0:
            print("📤 Loading documents into RAG system...")
            documents = knowledge_manager.get_all_documents()
            if documents:
                doc_ids = rag_system.add_documents(documents)
                print(f"Added {len(doc_ids)} documents to RAG system")
                rag_stats = rag_system.get_stats()
                print(f"Updated RAG stats: {rag_stats}")
        
        # Test retrieval
        print("\n🔎 Testing document retrieval...")
        test_query = "Liverpool recent form"
        results = rag_system.retrieve_relevant_documents(test_query, k=3)
        print(f"Query: '{test_query}'")
        print(f"Retrieved {len(results)} documents:")
        for i, result in enumerate(results):
            print(f"  {i+1}. Source: {result['source']}")
            print(f"     Content: {result['content'][:100]}...")
        
        # Test betting chatbot
        print("\n🤖 Testing Betting Chatbot...")
        betting_bot = get_betting_chatbot()
        final_stats = betting_bot.get_knowledge_stats()
        print(f"Betting bot knowledge stats: {final_stats}")
        
        print("\n✅ All tests passed! System is ready.")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_chat():
    """Test a simple chat interaction"""
    print("\n💬 Testing Simple Chat Interaction...")
    
    try:
        from chatbots.betting_bot import get_betting_chatbot
        
        betting_bot = get_betting_chatbot()
        
        # Simulate a test user
        test_user_id = 1
        test_session_id = "test_session_123"
        test_message = "Tell me about Liverpool's recent performance"
        
        print(f"User query: '{test_message}'")
        
        result = betting_bot.chat(
            message=test_message,
            user_id=test_user_id,
            session_id=test_session_id
        )
        
        print(f"Response: {result['response'][:200]}...")
        print(f"Query category: {result['query_category']}")
        print(f"Context sources: {result['context_sources']}")
        
        print("✅ Chat test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Knowledge Base and RAG System Tests...\n")
    
    # Test initialization
    init_success = test_knowledge_initialization()
    
    if init_success:
        # Test chat functionality
        chat_success = test_simple_chat()
        
        if chat_success:
            print("\n🎉 All tests completed successfully!")
            print("The betting chatbot with RAG system is ready to use.")
        else:
            print("\n⚠️  Initialization succeeded but chat test failed.")
            sys.exit(1)
    else:
        print("\n❌ Initialization tests failed.")
        sys.exit(1)