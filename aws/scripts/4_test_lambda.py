#!/usr/bin/env python3
"""
Test Lambda function with sample embedding
Run: python aws/scripts/4_test_lambda.py
"""
import json
import boto3
import numpy as np

FUNCTION_NAME = "pharma-context-provider"
REGION = "eu-west-2"

def test_lambda():
    """Test Lambda with sample query"""
    lambda_client = boto3.client('lambda', region_name=REGION)
    
    # Generate sample embedding (1536 dimensions)
    sample_embedding = np.random.rand(1536).tolist()
    
    # Test payload
    payload = {
        'embedding': sample_embedding,
        'n_results': 5,
        'filter': {'category': 'GAMP-5'}  # Optional filter
    }
    
    print(f"🧪 Testing Lambda: {FUNCTION_NAME}")
    print(f"📊 Query: {len(sample_embedding)} dimensions, top 5 results")
    
    # Invoke Lambda
    response = lambda_client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    # Parse response
    result = json.loads(response['Payload'].read())
    
    print(f"\n✅ Status: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"📄 Found {body['count']} documents")
        
        results = body['results']
        for i, (doc, meta, dist) in enumerate(zip(
            results['documents'],
            results['metadatas'],
            results['distances']
        )):
            print(f"\n{i+1}. Distance: {dist:.4f}")
            print(f"   Metadata: {meta}")
            print(f"   Preview: {doc[:100]}...")
    else:
        print(f"❌ Error: {result['body']}")
    
    # Print execution metrics
    print(f"\n📊 Execution Metrics:")
    print(f"   Duration: {response['ResponseMetadata']['HTTPHeaders'].get('x-amzn-remapped-content-length', 'N/A')}")
    print(f"   Billed Duration: {response.get('ExecutedVersion', 'N/A')}")

if __name__ == "__main__":
    test_lambda()
