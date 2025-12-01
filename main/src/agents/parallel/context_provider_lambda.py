"""
Context Provider Agent - Lambda Integration
Replaces local ChromaDB with AWS Lambda backend
"""
import os
import json
import boto3
from typing import List, Dict, Any, Optional
from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding

class LambdaContextProvider:
    """Context provider using AWS Lambda + ChromaDB"""
    
    def __init__(
        self,
        function_name: str = "pharma-context-provider",
        region: str = "eu-central-1",
        embedding_model: Optional[BaseEmbedding] = None
    ):
        self.function_name = function_name
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.embedding_model = embedding_model or OpenAIEmbedding(
            model="text-embedding-ada-002",
            api_key=os.environ.get('OPENAI_API_KEY')
        )
    
    def get_context(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve regulatory context from Lambda
        
        Args:
            query: Natural language query
            n_results: Number of results to return
            filter_metadata: Optional metadata filter (e.g., {"category": "GAMP-5"})
        
        Returns:
            List of context documents with metadata
        """
        # Generate embedding
        embedding = self.embedding_model.get_text_embedding(query)
        
        # Prepare Lambda payload
        payload = {
            'embedding': embedding,
            'n_results': n_results
        }
        
        if filter_metadata:
            payload['filter'] = filter_metadata
        
        # Invoke Lambda
        response = self.lambda_client.invoke(
            FunctionName=self.function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        result = json.loads(response['Payload'].read())
        
        if result['statusCode'] != 200:
            error = json.loads(result['body'])
            raise Exception(f"Lambda error: {error.get('error', 'Unknown')}")
        
        body = json.loads(result['body'])
        results = body['results']
        
        # Format results
        contexts = []
        for doc, meta, dist in zip(
            results['documents'],
            results['metadatas'],
            results['distances']
        ):
            contexts.append({
                'content': doc,
                'metadata': meta,
                'distance': dist
            })
        
        return contexts
    
    def get_gamp5_context(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Get GAMP-5 specific context"""
        return self.get_context(
            query,
            n_results=n_results,
            filter_metadata={'category': 'GAMP-5'}
        )
    
    def get_fda_context(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Get FDA 21 CFR Part 11 context"""
        return self.get_context(
            query,
            n_results=n_results,
            filter_metadata={'category': 'FDA'}
        )


# Backward compatibility wrapper
class ContextProviderAgent:
    """Wrapper to maintain compatibility with existing code"""
    
    def __init__(self, use_lambda: bool = True):
        if use_lambda:
            self.provider = LambdaContextProvider()
        else:
            # Fallback to local ChromaDB
            from .context_provider import ContextProviderAgent as LocalProvider
            self.provider = LocalProvider()
    
    def get_context(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        return self.provider.get_context(query, **kwargs)


# Example usage
if __name__ == "__main__":
    # Initialize provider
    provider = LambdaContextProvider()
    
    # Query for GAMP-5 context
    contexts = provider.get_gamp5_context(
        "What are the requirements for Category 5 software validation?"
    )
    
    print(f"Found {len(contexts)} relevant documents:")
    for i, ctx in enumerate(contexts, 1):
        print(f"\n{i}. Distance: {ctx['distance']:.4f}")
        print(f"   Source: {ctx['metadata'].get('source', 'Unknown')}")
        print(f"   Preview: {ctx['content'][:150]}...")
