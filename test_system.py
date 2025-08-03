#!/usr/bin/env python3
"""
Test script to verify the account creation system is working properly.
This script tests individual components without actually creating accounts.
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path to allow absolute imports
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing imports...")
    
    try:
        from config.config import Config
        print("✅ Config imported successfully")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from modules.database import Database
        print("✅ Database module imported successfully")
    except Exception as e:
        print(f"❌ Database import failed: {e}")
        return False
    
    try:
        from modules.profile_manager import ProfileManager
        print("✅ ProfileManager imported successfully")
    except Exception as e:
        print(f"❌ ProfileManager import failed: {e}")
        return False
    
    try:
        from utils.identity_generator import IdentityGenerator
        print("✅ IdentityGenerator imported successfully")
    except Exception as e:
        print(f"❌ IdentityGenerator import failed: {e}")
        return False
    
    try:
        from utils.notifier import Notifier
        print("✅ Notifier imported successfully")
    except Exception as e:
        print(f"❌ Notifier import failed: {e}")
        return False
    
    try:
        from utils.face_generator import FaceGenerator
        print("✅ FaceGenerator imported successfully")
    except Exception as e:
        print(f"❌ FaceGenerator import failed: {e}")
        return False
    
    return True

def test_identity_generation():
    """Test identity generation functionality"""
    print("\nTesting identity generation...")
    
    try:
        from utils.identity_generator import IdentityGenerator
        
        identity_gen = IdentityGenerator()
        identity = identity_gen.generate_identity()
        
        required_fields = ['username', 'password', 'email', 'first_name', 'last_name']
        for field in required_fields:
            if field not in identity:
                print(f"❌ Missing field in identity: {field}")
                return False
            if not identity[field]:
                print(f"❌ Empty field in identity: {field}")
                return False
        
        print(f"✅ Identity generated successfully: {identity['username']}")
        return True
        
    except Exception as e:
        print(f"❌ Identity generation failed: {e}")
        return False

def test_profile_generation():
    """Test profile generation functionality"""
    print("\nTesting profile generation...")
    
    try:
        from modules.profile_manager import ProfileManager
        
        profile_manager = ProfileManager()
        profile = profile_manager.generate_full_profile()
        
        required_sections = ['basic', 'personal', 'contact', 'digital', 'media']
        for section in required_sections:
            if section not in profile:
                print(f"❌ Missing section in profile: {section}")
                return False
        
        print(f"✅ Profile generated successfully: {profile['basic']['username']}")
        return True
        
    except Exception as e:
        print(f"❌ Profile generation failed: {e}")
        return False

def test_face_generation():
    """Test face generation functionality"""
    print("\nTesting face generation...")
    
    try:
        from utils.face_generator import FaceGenerator
        
        face_gen = FaceGenerator()
        # Just test that the model loads without crashing
        print("✅ FaceGenerator initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Face generation failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("\nTesting database connection...")
    
    try:
        from modules.database import Database
        
        db = Database()
        # Try to create table (this will test the connection)
        result = db.create_table()
        
        if result:
            print("✅ Database connection and table creation successful")
            return True
        else:
            print("❌ Database table creation failed")
            return False
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_notifier():
    """Test notification system"""
    print("\nTesting notification system...")
    
    try:
        from utils.notifier import Notifier
        
        notifier = Notifier()
        notifier.send_alert("Test notification from system test")
        
        print("✅ Notifier working successfully")
        return True
        
    except Exception as e:
        print(f"❌ Notifier failed: {e}")
        return False

def test_identity_traversal():
    """Test identity traversal functionality"""
    print("\nTesting identity traversal...")
    
    try:
        from modules.profile_manager import ProfileManager
        from utils.identity_generator import IdentityGenerator
        
        profile_manager = ProfileManager()
        identity_gen = IdentityGenerator()
        
        # Generate a base profile
        base_profile = profile_manager.generate_full_profile(seed=42)
        
        # Test traversal
        identity_graph, traversal_path = identity_gen.traverse_namespace(
            base_profile,
            profile_manager,
            depth=3,
            variation_strength='medium'
        )
        
        if len(traversal_path) > 0 and len(identity_graph) > 0:
            print(f"✅ Identity traversal successful: {len(traversal_path)} identities generated")
            return True
        else:
            print("❌ Identity traversal failed: no identities generated")
            return False
        
    except Exception as e:
        print(f"❌ Identity traversal failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting system tests...\n")
    
    tests = [
        test_imports,
        test_identity_generation,
        test_profile_generation,
        test_face_generation,
        test_database_connection,
        test_notifier,
        test_identity_traversal
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for production.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)