"""
Knowledge Base Demo using Chroma MCP

This script demonstrates how to build a practical knowledge management system 
using Chroma MCP for document storage, retrieval, and analysis.

Features:
- Document categorization and storage
- Cross-collection semantic search
- Document analysis using sequential thinking
- Knowledge extraction and relationship mapping
"""

import json
import time
import uuid
from datetime import datetime
import sys

def use_mcp_tool(server_name, tool_name, arguments):
    """Use an MCP tool with the given arguments."""
    result = {}  # This would normally call the MCP tool using the MCP client
    print(f"[MCP] Using {tool_name} on {server_name} with: {json.dumps(arguments, indent=2)}")
    return result

# Wrapper functions for Chroma MCP tools
def chroma_create_collection(collection_name, **kwargs):
    """Create a new Chroma collection."""
    return use_mcp_tool(
        "chroma-mcp", 
        "chroma_create_collection", 
        {"collection_name": collection_name, **kwargs}
    )

def chroma_add_documents(collection_name, documents, metadatas=None, ids=None):
    """Add documents to a Chroma collection."""
    return use_mcp_tool(
        "chroma-mcp", 
        "chroma_add_documents", 
        {
            "collection_name": collection_name,
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids
        }
    )

def chroma_query_documents(collection_name, query_texts, n_results=5, where=None):
    """Query documents from a Chroma collection with optional filtering."""
    return use_mcp_tool(
        "chroma-mcp", 
        "chroma_query_documents", 
        {
            "collection_name": collection_name,
            "query_texts": query_texts,
            "n_results": n_results,
            "where": where
        }
    )

def chroma_sequential_thinking(thought, thoughtNumber, totalThoughts, nextThoughtNeeded, **kwargs):
    """Use sequential thinking for complex analysis."""
    return use_mcp_tool(
        "chroma-mcp", 
        "chroma_sequential_thinking", 
        {
            "thought": thought,
            "thoughtNumber": thoughtNumber,
            "totalThoughts": totalThoughts,
            "nextThoughtNeeded": nextThoughtNeeded,
            **kwargs
        }
    )

def print_header(title):
    """Print a formatted header."""
    width = 80
    print("\n" + "=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width + "\n")

class KnowledgeBase:
    """A simple knowledge management system using Chroma MCP."""
    
    def __init__(self):
        """Initialize the knowledge base."""
        self.collections = {
            "technical_docs": "Technical documentation and code examples",
            "research_papers": "Scientific papers and research articles",
            "business_docs": "Business reports, plans, and analyses",
            "knowledge_graph": "Extracted concepts and relationships"
        }
        self.session_id = f"kb_session_{str(uuid.uuid4())[:8]}"
        
    def setup_collections(self):
        """Set up the knowledge base collections."""
        print_header("INITIALIZING KNOWLEDGE BASE")
        
        for name, description in self.collections.items():
            print(f"Creating collection: {name} - {description}")
            chroma_create_collection(
                collection_name=name,
                hnsw_space="cosine"  # Use cosine similarity for semantic search
            )
            
        print("\nKnowledge base collections created successfully.")
        
    def add_technical_documentation(self):
        """Add sample technical documentation."""
        print_header("ADDING TECHNICAL DOCUMENTATION")
        
        documents = [
            """
            # Python Data Processing Pipeline
            
            This document describes how to build a data processing pipeline using Python.
            
            ## Components
            
            1. Data ingestion: Use pandas to read CSV, JSON, or SQL data
            2. Data cleaning: Handle missing values, outliers, and duplicates
            3. Transformation: Apply calculations, aggregations, and feature engineering
            4. Analysis: Use statistical methods to extract insights
            5. Visualization: Create charts and graphs with matplotlib or seaborn
            
            ## Example Code
            
            ```python
            import pandas as pd
            
            # Ingest data
            df = pd.read_csv('data.csv')
            
            # Clean data
            df = df.dropna()
            
            # Transform data
            df['new_feature'] = df['feature1'] / df['feature2']
            
            # Analyze
            summary = df.describe()
            ```
            """,
            
            """
            # Kubernetes Deployment Guide
            
            This guide explains how to deploy applications using Kubernetes.
            
            ## Architecture
            
            Kubernetes consists of:
            - Control plane: API server, scheduler, controller manager
            - Worker nodes: Kubelet, container runtime, kube-proxy
            
            ## Deployment Steps
            
            1. Create a Dockerfile for your application
            2. Build and push your container image
            3. Define Kubernetes resources (Deployments, Services)
            4. Apply configurations using kubectl
            
            ## Example YAML
            
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: my-app
            spec:
              replicas: 3
              selector:
                matchLabels:
                  app: my-app
              template:
                metadata:
                  labels:
                    app: my-app
                spec:
                  containers:
                  - name: my-app
                    image: my-image:latest
                    ports:
                    - containerPort: 8080
            ```
            """,
            
            """
            # React Component Design Patterns
            
            This document covers best practices for designing React components.
            
            ## Component Types
            
            1. Presentational Components: Focused on UI, receive data via props
            2. Container Components: Manage state and data fetching
            3. Higher-Order Components (HOCs): Enhance components with additional functionality
            4. Hooks: Use state and other React features in functional components
            
            ## Code Example: Custom Hook
            
            ```jsx
            import { useState, useEffect } from 'react';
            
            function useFetch(url) {
              const [data, setData] = useState(null);
              const [loading, setLoading] = useState(true);
              const [error, setError] = useState(null);
              
              useEffect(() => {
                async function fetchData() {
                  try {
                    const response = await fetch(url);
                    const json = await response.json();
                    setData(json);
                  } catch (error) {
                    setError(error);
                  } finally {
                    setLoading(false);
                  }
                }
                
                fetchData();
              }, [url]);
              
              return { data, loading, error };
            }
            ```
            """
        ]
        
        metadatas = [
            {
                "title": "Python Data Processing Pipeline",
                "type": "guide",
                "technology": "python",
                "tags": ["data", "python", "pandas"]
            },
            {
                "title": "Kubernetes Deployment Guide",
                "type": "guide",
                "technology": "kubernetes",
                "tags": ["kubernetes", "containers", "deployment"]
            },
            {
                "title": "React Component Design Patterns",
                "type": "patterns",
                "technology": "react",
                "tags": ["react", "javascript", "components"]
            }
        ]
        
        chroma_add_documents(
            collection_name="technical_docs",
            documents=documents,
            metadatas=metadatas
        )
        
        print("Added technical documentation to the knowledge base.")
        
    def add_research_papers(self):
        """Add sample research papers."""
        print_header("ADDING RESEARCH PAPERS")
        
        documents = [
            """
            # Attention Is All You Need
            
            ## Abstract
            
            The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.
            
            ## Introduction
            
            Recurrent neural networks, long short-term memory and gated recurrent neural networks in particular, have been firmly established as state of the art approaches in sequence modeling and transduction problems such as language modeling and machine translation. Numerous efforts have been made to improve recurrent language models.
            
            Self-attention, sometimes called intra-attention, is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence. Self-attention has been used successfully in a variety of tasks including reading comprehension, abstractive summarization, textual entailment and learning task-independent sentence representations.
            """,
            
            """
            # Distributed Representations of Words and Phrases and their Compositionality
            
            ## Abstract
            
            The recently introduced continuous Skip-gram model is an efficient method for learning high-quality distributed vector representations that capture a large number of precise syntactic and semantic word relationships. In this paper we present several extensions that improve both the quality of the vectors and the training speed. By subsampling of the frequent words we obtain significant speedup and also learn more regular word representations. We also describe a simple alternative to the hierarchical softmax called negative sampling.
            
            ## Introduction
            
            Linguistically, words can be broadly categorized as content words (nouns, verbs, adjectives, and most adverbs) and function words (pronouns, prepositions, conjunctions, etc). Content words usually carry rich semantic content, and their representations can be effectively learned from their contexts. However, the meanings of function words are more subtle and depend more on the grammatical structure.
            """,
            
            """
            # Deep Residual Learning for Image Recognition
            
            ## Abstract
            
            Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions. We provide comprehensive empirical evidence showing that these residual networks are easier to optimize, and can gain accuracy from considerably increased depth.
            
            ## Introduction
            
            Deep convolutional neural networks have led to a series of breakthroughs for image classification. Deep networks naturally integrate low/mid/high-level features and classifiers in an end-to-end multi-layer fashion, and the "levels" of features can be enriched by the number of stacked layers. Recent evidence suggests that network depth is of crucial importance.
            """
        ]
        
        metadatas = [
            {
                "title": "Attention Is All You Need",
                "authors": "Vaswani et al.",
                "year": 2017,
                "field": "natural language processing",
                "tags": ["transformers", "attention", "nlp"]
            },
            {
                "title": "Distributed Representations of Words and Phrases and their Compositionality",
                "authors": "Mikolov et al.",
                "year": 2013,
                "field": "natural language processing",
                "tags": ["word2vec", "embeddings", "nlp"]
            },
            {
                "title": "Deep Residual Learning for Image Recognition",
                "authors": "He et al.",
                "year": 2015,
                "field": "computer vision",
                "tags": ["resnet", "cnn", "computer vision"]
            }
        ]
        
        chroma_add_documents(
            collection_name="research_papers",
            documents=documents,
            metadatas=metadatas
        )
        
        print("Added research papers to the knowledge base.")
        
    def add_business_documents(self):
        """Add sample business documents."""
        print_header("ADDING BUSINESS DOCUMENTS")
        
        documents = [
            """
            # Market Analysis Report: AI Software Industry
            
            ## Executive Summary
            
            The global AI software market is projected to grow from $62.5 billion in 2022 to $126 billion by 2025, at a CAGR of 26.3%. This growth is driven by increasing adoption across industries, advancements in deep learning, and the proliferation of cloud-based AI solutions.
            
            ## Key Findings
            
            1. Enterprise AI adoption increased by 270% over the past four years
            2. 72% of business leaders consider AI a "business advantage"
            3. Healthcare, financial services, and retail show the highest growth rates
            4. Small and medium businesses are increasingly adopting AI solutions
            
            ## Competitive Landscape
            
            Major players include:
            - Microsoft
            - Google
            - IBM
            - Amazon
            - OpenAI
            - Anthropic
            
            The market is experiencing rapid consolidation with established tech companies acquiring AI startups.
            """,
            
            """
            # Strategic Plan 2023-2025: Digital Transformation Initiative
            
            ## Vision
            
            To become a fully digitalized, data-driven organization that leverages technology to enhance customer experience, optimize operations, and create new business models.
            
            ## Strategic Objectives
            
            1. Modernize core IT infrastructure and migrate 80% of applications to the cloud by 2024
            2. Implement AI-powered analytics platforms across all business units
            3. Develop digital skills among 95% of employees through comprehensive training programs
            4. Launch at least 3 new digital products or services annually
            
            ## Implementation Roadmap
            
            ### Phase 1 (2023 Q1-Q2)
            - Complete IT infrastructure assessment
            - Develop cloud migration strategy
            - Establish Digital Center of Excellence
            
            ### Phase 2 (2023 Q3-2024 Q2)
            - Execute cloud migration
            - Deploy AI and analytics platforms
            - Launch digital upskilling program
            
            ### Phase 3 (2024 Q3-2025 Q4)
            - Scale digital initiatives
            - Optimize and refine digital processes
            - Evaluate outcomes and plan next phase
            """,
            
            """
            # Quarterly Financial Report: Q2 2023
            
            ## Financial Highlights
            
            - Revenue: $128.5 million (↑18% YoY)
            - Gross Margin: 65.3% (↑2.1% YoY)
            - Operating Income: $32.1 million (↑22% YoY)
            - Net Income: $24.8 million (↑19% YoY)
            - EPS: $1.24 (↑17% YoY)
            
            ## Revenue by Segment
            
            - Software & Services: $78.2 million (↑23% YoY)
            - Hardware: $32.4 million (↑8% YoY)
            - Consulting: $17.9 million (↑14% YoY)
            
            ## Outlook
            
            We are raising our full-year guidance:
            - Revenue: $510-530 million (previously $490-510 million)
            - Operating Margin: 25-27% (previously 23-25%)
            - EPS: $4.95-$5.15 (previously $4.75-$4.95)
            
            We expect continued strong performance in the Software & Services segment driven by our new AI-enhanced product line and expansion into international markets.
            """
        ]
        
        metadatas = [
            {
                "title": "Market Analysis Report: AI Software Industry",
                "type": "market analysis",
                "department": "research",
                "date": "2023-02-15",
                "tags": ["ai", "market research", "industry analysis"]
            },
            {
                "title": "Strategic Plan 2023-2025: Digital Transformation Initiative",
                "type": "strategic plan",
                "department": "executive",
                "date": "2023-01-10",
                "tags": ["strategy", "digital transformation", "planning"]
            },
            {
                "title": "Quarterly Financial Report: Q2 2023",
                "type": "financial report",
                "department": "finance",
                "date": "2023-07-28",
                "tags": ["financial", "quarterly report", "earnings"]
            }
        ]
        
        chroma_add_documents(
            collection_name="business_docs",
            documents=documents,
            metadatas=metadatas
        )
        
        print("Added business documents to the knowledge base.")
        
    def analyze_documents(self):
        """Analyze documents using sequential thinking."""
        print_header("ANALYZING DOCUMENTS WITH SEQUENTIAL THINKING")
        
        # First thought: Planning the analysis
        thought1 = """
        I need to analyze the knowledge base to extract key insights across different document types.
        
        The knowledge base contains three main categories:
        1. Technical documentation (Python, Kubernetes, React)
        2. Research papers (Transformers, Word2Vec, ResNet)
        3. Business documents (Market analysis, Strategic plan, Financial report)
        
        My approach will be to:
        1. Identify common themes and technologies across documents
        2. Analyze how research papers relate to technical implementations
        3. Understand business implications of the technical and research content
        4. Create a knowledge graph of key concepts and their relationships
        
        I'll start by identifying the key technologies and concepts in each category.
        """
        
        thought1_result = chroma_sequential_thinking(
            thought=thought1,
            thoughtNumber=1,
            totalThoughts=4,
            nextThoughtNeeded=True,
            sessionId=self.session_id
        )
        
        # Second thought: Extracting key concepts
        thought2 = """
        After reviewing the documents, I can identify these key concepts:
        
        Technical Domain:
        - Data processing: Python, pandas, data pipelines
        - Infrastructure: Kubernetes, containers, deployment
        - Frontend: React, components, hooks
        
        Research Domain:
        - NLP: Transformers, attention mechanisms, word embeddings
        - Computer Vision: ResNet, CNNs, deep learning
        
        Business Domain:
        - Market trends: AI software growth, industry adoption
        - Strategy: Digital transformation, cloud migration
        - Performance: Revenue growth, segment analysis
        
        I'm seeing interesting connections between research papers and technical implementations:
        - Transformer architecture (research) → potential NLP applications (technical)
        - Word embeddings (research) → data processing pipelines (technical)
        - ResNet (research) → potential computer vision applications (technical)
        
        The business documents indicate strong growth in AI adoption, which relates directly 
        to the technical and research domains covered in the other documents.
        """
        
        thought2_result = chroma_sequential_thinking(
            thought=thought2,
            thoughtNumber=2,
            totalThoughts=4,
            nextThoughtNeeded=True,
            sessionId=self.session_id
        )
        
        # Third thought: Building relationships
        thought3 = """
        Now I'll map the relationships between key concepts to form a knowledge graph:
        
        Core Technology Relationships:
        - AI/ML serves as the foundation connecting most concepts
        - NLP technologies (transformers, embeddings) → Python data processing
        - Cloud infrastructure → Kubernetes deployment
        - Frontend frameworks → React components
        
        Business Implications:
        - Strategic plan emphasizes cloud migration → relates to Kubernetes documentation
        - AI market analysis shows growth → connects to transformer and ResNet research
        - Financial growth in software segment → aligns with all technical documentation
        
        Potential Applications (cross-domain):
        - Transformer models → NLP services → AI software market opportunity
        - ResNet architecture → Computer vision products → Digital transformation initiative
        - Word embeddings → Data analytics → Strategic business insights
        
        This analysis reveals how the research concepts can be implemented using the 
        technical approaches described, ultimately driving the business outcomes 
        highlighted in the strategic and financial documents.
        """
        
        thought3_result = chroma_sequential_thinking(
            thought=thought3,
            thoughtNumber=3,
            totalThoughts=4,
            nextThoughtNeeded=True,
            sessionId=self.session_id
        )
        
        # Fourth thought: Conclusions and recommendations
        thought4 = """
        Based on the comprehensive analysis of the knowledge base, I can draw these conclusions:
        
        1. The knowledge base contains a coherent ecosystem of information spanning from
           cutting-edge research through technical implementation to business applications.
           
        2. There are clear pathways from research concepts to technical implementation:
           - Transformer architecture → Python NLP libraries → AI-powered applications
           - ResNet → Computer vision frameworks → Image recognition products
           
        3. The business documents align well with the technical capabilities described,
           particularly in AI software and digital transformation areas.
           
        4. Key opportunity areas identified through this analysis:
           - NLP services leveraging transformer architecture
           - Cloud-native AI applications using Kubernetes
           - Component-based frontend systems for data visualization
           
        5. Recommended knowledge graph structure:
           - Core AI/ML concepts as central nodes
           - Branching into specific technical implementations
           - Connected to business applications and market opportunities
           - Metadata tags for cross-domain search
           
        This knowledge base structure provides a powerful foundation for connecting
        research innovations to technical implementations and business value.
        """
        
        thought4_result = chroma_sequential_thinking(
            thought=thought4,
            thoughtNumber=4,
            totalThoughts=4,
            nextThoughtNeeded=False,
            sessionId=self.session_id,
            sessionSummary="Comprehensive analysis of knowledge base spanning research papers, technical documentation, and business documents. Identified key relationships between concepts across domains and mapped potential pathways from research innovations to business value.",
            keyThoughts=[1, 3, 4]
        )
        
        print("Completed document analysis using sequential thinking.")
        
    def cross_collection_search(self):
        """Perform semantic search across all collections."""
        print_header("CROSS-COLLECTION SEMANTIC SEARCH")
        
        # Different search queries to demonstrate semantic search capabilities
        queries = [
            "machine learning models for natural language",
            "cloud deployment strategies",
            "financial performance of AI companies",
            "frontend development patterns",
            "deep learning architectures"
        ]
        
        for query in queries:
            print(f"\nSEARCH QUERY: '{query}'\n")
            
            # Search across all collections
            for collection_name, description in self.collections.items():
                if collection_name != "knowledge_graph":  # Skip the knowledge graph for searching
                    print(f"Results from {collection_name} ({description}):")
                    
                    results = chroma_query_documents(
                        collection_name=collection_name,
                        query_texts=[query],
                        n_results=1  # Get top result from each collection
                    )
                    
                    # Print simplified results (in actual implementation, this would show the actual results)
                    print("  [Found matching documents with relevant content]")
                    print()
        
        print("\nCross-collection search complete.")
        
    def run_demo(self):
        """Run the full knowledge base demo."""
        print_header("KNOWLEDGE BASE DEMO")
        print(f"Demo running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Using session ID: {self.session_id}")
        
        try:
            # Step 1: Set up collections
            self.setup_collections()
            
            # Step 2: Add sample documents
            self.add_technical_documentation()
            self.add_research_papers()
            self.add_business_documents()
            
            # Step 3: Analyze documents using sequential thinking
            self.analyze_documents()
            
            # Step 4: Demonstrate cross-collection search
            self.cross_collection_search()
            
            print("\nKnowledge base demo completed successfully!")
            
        except Exception as e:
            print(f"\nERROR: {str(e)}")
            print("Demo did not complete successfully.")

# Main function
if __name__ == "__main__":
    print("""
Chroma MCP Knowledge Base Demo

This script demonstrates how to build a practical knowledge management system
using Chroma MCP for document storage, retrieval, and analysis.

NOTE: This is a demonstration script that simulates interaction with the MCP tools.
To run with actual MCP tools, the use_mcp_tool function would need to be replaced
with actual calls to the MCP client.

Usage:
    python knowledge_base_demo.py --run     Run the full demonstration
    python knowledge_base_demo.py           Show this help message
    """)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        kb = KnowledgeBase()
        kb.run_demo()
