#!/usr/bin/env python3
"""
Test script to verify MongoDB connection.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

def test_mongodb_connection():
    """Test MongoDB connection with the provided credentials."""
    try:
        from pymongo import MongoClient
        
        # Get connection string from environment
        mongo_uri = os.environ.get('MONGO_URI')
        if not mongo_uri:
            print("ERROR: MONGO_URI not found in environment variables")
            return False
            
        print(f"Testing MongoDB connection...")
        print(f"URI: {mongo_uri[:50]}...")  # Show only first 50 chars for security
        
        # Test connection
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Test server selection
        client.server_info()
        print("✓ MongoDB connection successful!")
        
        # Test database access
        db_name = os.environ.get('MONGO_DB', 'fintech_forecasting')
        db = client[db_name]
        
        # List collections
        collections = db.list_collection_names()
        print(f"✓ Database '{db_name}' accessible")
        print(f"✓ Collections: {collections}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return False

def test_environment_variables():
    """Test if all required environment variables are set."""
    print("Testing environment variables...")
    
    required_vars = ['MONGO_URI', 'USE_MONGO', 'MONGO_DB']
    all_set = True
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if var == 'MONGO_URI':
                print(f"✓ {var}: {value[:50]}...")  # Show only first 50 chars
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: Not set")
            all_set = False
    
    return all_set

if __name__ == "__main__":
    print("=" * 60)
    print("MongoDB Connection Test")
    print("=" * 60)
    
    # Test environment variables
    env_ok = test_environment_variables()
    print()
    
    if env_ok:
        # Test MongoDB connection
        conn_ok = test_mongodb_connection()
        
        print("\n" + "=" * 60)
        if conn_ok:
            print("✓ All tests passed! MongoDB is ready to use.")
        else:
            print("✗ MongoDB connection test failed.")
            print("Please check your credentials and network connection.")
    else:
        print("\n" + "=" * 60)
        print("✗ Environment variables not properly set.")
        print("Please check your config.env file.")
    
    print("=" * 60)
