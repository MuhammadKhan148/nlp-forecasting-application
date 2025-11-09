#!/usr/bin/env python3
"""
Quick MongoDB Local Connection Check
This script checks if MongoDB is running locally on port 27017.
"""

import socket
import sys

def check_mongodb_running():
    """Check if MongoDB is running on localhost:27017."""
    try:
        # Try to connect to MongoDB port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 27017))
        sock.close()
        
        if result == 0:
            print("✓ MongoDB is running on localhost:27017")
            return True
        else:
            print("✗ MongoDB is not running on localhost:27017")
            return False
            
    except Exception as e:
        print(f"✗ Error checking MongoDB: {e}")
        return False

def main():
    print("=" * 50)
    print("MongoDB Local Connection Check")
    print("=" * 50)
    
    if check_mongodb_running():
        print("\n✓ MongoDB is ready for connection!")
        print("You can now run the comprehensive test:")
        print("  python test_mongodb_comprehensive.py")
    else:
        print("\n✗ MongoDB is not running!")
        print("\nTo start MongoDB:")
        print("1. Install MongoDB Community Server")
        print("2. Start MongoDB service:")
        print("   - Windows: net start MongoDB")
        print("   - macOS: brew services start mongodb-community")
        print("   - Linux: sudo systemctl start mongod")
        print("\nOr use MongoDB Compass to connect to:")
        print("  mongodb://localhost:27017")

if __name__ == "__main__":
    main()

