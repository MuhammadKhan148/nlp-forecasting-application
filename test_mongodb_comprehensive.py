#!/usr/bin/env python3
"""
Comprehensive MongoDB Connection Test
This script will test the connection and insert sample data that you can verify in MongoDB Compass.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

def test_mongodb_connection():
    """Test MongoDB connection and basic operations."""
    try:
        from pymongo import MongoClient
        
        # Get connection string from environment
        mongo_uri = os.environ.get('MONGO_URI')
        db_name = os.environ.get('MONGO_DB', 'nlp')
        
        if not mongo_uri:
            print("ERROR: MONGO_URI not found in environment variables")
            return False
            
        print("=" * 60)
        print("MongoDB Connection Test")
        print("=" * 60)
        print(f"Connection URI: {mongo_uri}")
        print(f"Database Name: {db_name}")
        print()
        
        # Test connection
        print("1. Testing MongoDB connection...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Test server selection
        server_info = client.server_info()
        print(f"✓ Connected to MongoDB version: {server_info['version']}")
        
        # Test database access
        db = client[db_name]
        print(f"✓ Database '{db_name}' accessible")
        
        # List existing collections
        collections = db.list_collection_names()
        print(f"✓ Existing collections: {collections}")
        
        return client, db
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return False, None

def insert_test_data(db):
    """Insert sample financial data for testing."""
    print("\n2. Inserting test data...")
    
    try:
        # Sample historical price data
        historical_data = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(30):
            date = base_date + timedelta(days=i)
            price = 150 + (i * 0.5) + (i % 3)  # Simulate price movement
            
            record = {
                'symbol': 'TEST',
                'date': date.strftime('%Y-%m-%d'),
                'open': round(price, 2),
                'high': round(price + 2, 2),
                'low': round(price - 1, 2),
                'close': round(price + 0.5, 2),
                'volume': 1000000 + (i * 10000),
                'return_1d': round(0.01 + (i % 5) * 0.005, 4),
                'vol_5d': round(0.02 + (i % 3) * 0.01, 4),
                'sma_5': round(price - 1, 2),
                'sma_20': round(price - 2, 2)
            }
            historical_data.append(record)
        
        # Insert historical data
        collection = db.historical_prices
        result = collection.insert_many(historical_data)
        print(f"✓ Inserted {len(result.inserted_ids)} historical price records")
        
        # Sample sentiment data
        sentiment_data = []
        for i in range(30):
            date = base_date + timedelta(days=i)
            
            record = {
                'symbol': 'TEST',
                'date': date.strftime('%Y-%m-%d'),
                'sent_count': 50 + (i % 10),
                'sent_mean': round(0.1 + (i % 7) * 0.05, 3),
                'sent_median': round(0.15 + (i % 5) * 0.03, 3),
                'sent_std': round(0.2 + (i % 3) * 0.1, 3),
                'sent_pos_share': round(0.4 + (i % 6) * 0.1, 3),
                'sent_neg_share': round(0.3 + (i % 4) * 0.05, 3)
            }
            sentiment_data.append(record)
        
        # Insert sentiment data
        collection = db.sentiment_data
        result = collection.insert_many(sentiment_data)
        print(f"✓ Inserted {len(result.inserted_ids)} sentiment records")
        
        # Sample forecast data
        forecast_data = {
            'symbol': 'TEST',
            'model_name': 'test_model',
            'forecast_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'horizon_hours': 24,
            'predicted_open': 155.50,
            'predicted_high': 157.20,
            'predicted_low': 154.80,
            'predicted_close': 156.30,
            'confidence_lower': 155.00,
            'confidence_upper': 157.60,
            'created_at': datetime.utcnow().isoformat()
        }
        
        collection = db.forecasts
        result = collection.insert_one(forecast_data)
        print(f"✓ Inserted forecast record: {result.inserted_id}")
        
        # Sample model metrics
        metrics_data = {
            'symbol': 'TEST',
            'model_name': 'test_model',
            'rmse': 2.45,
            'mae': 1.89,
            'mape': 1.25,
            'train_samples': 25,
            'test_samples': 5,
            'parameters': {'window': 5, 'trend': 'add'},
            'updated_at': datetime.utcnow().isoformat()
        }
        
        collection = db.model_metrics
        result = collection.insert_one(metrics_data)
        print(f"✓ Inserted model metrics: {result.inserted_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error inserting test data: {e}")
        return False

def verify_data_in_compass(db):
    """Verify data can be retrieved and provide Compass instructions."""
    print("\n3. Verifying data retrieval...")
    
    try:
        # Count documents in each collection
        collections_to_check = ['historical_prices', 'sentiment_data', 'forecasts', 'model_metrics']
        
        for collection_name in collections_to_check:
            collection = db[collection_name]
            count = collection.count_documents({})
            print(f"✓ {collection_name}: {count} documents")
            
            # Show sample document
            if count > 0:
                sample = collection.find_one()
                print(f"  Sample document keys: {list(sample.keys())}")
        
        print("\n" + "=" * 60)
        print("MongoDB Compass Verification Instructions")
        print("=" * 60)
        print("1. Open MongoDB Compass")
        print("2. Connect to: mongodb://localhost:27017")
        print("3. Select database: nlp")
        print("4. You should see these collections:")
        print("   - historical_prices (TEST symbol data)")
        print("   - sentiment_data (TEST symbol sentiment)")
        print("   - forecasts (sample forecast)")
        print("   - model_metrics (sample metrics)")
        print("5. Click on any collection to view the data")
        print("6. Use filters like {'symbol': 'TEST'} to see test data")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"✗ Error verifying data: {e}")
        return False

def test_application_integration():
    """Test if the application can use MongoDB."""
    print("\n4. Testing application integration...")
    
    try:
        # Import the application's MongoDB class
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from database.mongo_db import MongoDatabase
        
        mongo_uri = os.environ.get('MONGO_URI')
        db = MongoDatabase(mongo_uri)
        
        # Test application methods
        symbols = db.get_available_symbols()
        print(f"✓ Available symbols: {symbols}")
        
        if 'TEST' in symbols:
            historical = db.get_historical_data('TEST', limit=5)
            print(f"✓ Retrieved {len(historical)} historical records")
            
            forecasts = db.get_forecasts('TEST')
            print(f"✓ Retrieved {len(forecasts)} forecast records")
            
            metrics = db.get_model_metrics('TEST')
            print(f"✓ Retrieved {len(metrics)} metric records")
        
        return True
        
    except Exception as e:
        print(f"✗ Application integration test failed: {e}")
        return False

def cleanup_test_data(db):
    """Clean up test data."""
    print("\n5. Cleaning up test data...")
    
    try:
        collections_to_clean = ['historical_prices', 'sentiment_data', 'forecasts', 'model_metrics']
        
        for collection_name in collections_to_clean:
            collection = db[collection_name]
            result = collection.delete_many({'symbol': 'TEST'})
            print(f"✓ Cleaned {result.deleted_count} documents from {collection_name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error cleaning up: {e}")
        return False

def main():
    """Main test function."""
    print("Starting comprehensive MongoDB test...")
    
    # Test connection
    client, db = test_mongodb_connection()
    if not client:
        return
    
    try:
        # Insert test data
        if insert_test_data(db):
            # Verify data
            verify_data_in_compass(db)
            
            # Test application integration
            test_application_integration()
            
            # Ask if user wants to keep test data
            print("\n" + "=" * 60)
            keep_data = input("Keep test data in MongoDB? (y/n): ").lower()
            if keep_data not in ['y', 'yes']:
                cleanup_test_data(db)
            else:
                print("✓ Test data kept in database")
        
    finally:
        client.close()
        print("\n✓ MongoDB connection closed")

if __name__ == "__main__":
    main()

