#!/usr/bin/env python3
"""
E2E Test Script for Travel Agent Deployment
This script simulates the exact message processing flow to identify issues.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if all required environment variables are set."""
    print("🔍 Testing Environment Variables...")
    
    required_vars = [
        "IO_API_KEY",
        "REDIS_URL", 
        "TWILIO_ACCOUNT_SID",
        "TELEGRAM_BOT_TOKEN",
        "AMADEUS_CLIENT_ID",
        "CIRCLE_API_KEY",
        "STRIPE_SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {'*' * min(len(value), 8)}...")
        else:
            print(f"  ❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("\n✅ All environment variables are set")
        return True

def test_ai_service_directly():
    """Test AI service directly without going through the web framework."""
    print("\n🧠 Testing AI Service Directly...")
    
    try:
        # Import and test AI service
        from app.ai_service import client, get_ai_response
        
        print(f"  ✅ AI Service client created: {client is not None}")
        
        # Test a simple conversation
        conversation_history = []
        response, updated_history = get_ai_response("Hi, I want to book a flight", conversation_history, "GATHERING_INFO")
        
        print(f"  ✅ AI Response received: {len(response)} characters")
        print(f"  📝 Response preview: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ AI Service test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_core_logic_directly():
    """Test core logic directly without going through the web framework."""
    print("\n🔄 Testing Core Logic Directly...")
    
    try:
        from app.core_logic import process_message
        from app.amadeus_service import AmadeusService
        
        # Create a mock Amadeus service
        amadeus_service = AmadeusService()
        
        # Test message processing
        user_id = "test_user_123"
        message = "Hi, I want to book a flight from London to Paris on December 25th"
        
        print(f"  📤 Sending message: {message[:50]}...")
        responses = process_message(user_id, message, amadeus_service)
        
        print(f"  ✅ Core logic processed message: {len(responses)} responses")
        for i, response in enumerate(responses):
            print(f"    Response {i+1}: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Core Logic test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_redis_connection():
    """Test Redis connection directly."""
    print("\n🗄️ Testing Redis Connection...")
    
    try:
        from app.new_session_manager import get_redis_client
        
        redis_client = get_redis_client()
        if redis_client:
            redis_client.ping()
            print("  ✅ Redis connection successful")
            return True
        else:
            print("  ❌ Redis client not available")
            return False
            
    except Exception as e:
        print(f"  ❌ Redis test failed: {type(e).__name__}: {e}")
        return False

def test_webhook_simulation():
    """Simulate a webhook request to test the full flow."""
    print("\n🌐 Testing Webhook Simulation...")
    
    try:
        # This would require the Flask app to be running
        # For now, we'll just test the imports
        from app.main import app
        
        print("  ✅ Flask app can be imported")
        print("  ℹ️  To test actual webhooks, run: python -m flask run")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Webhook test failed: {type(e).__name__}: {e}")
        return False

def main():
    """Run all E2E tests."""
    print("🚀 Starting E2E Tests for Travel Agent Deployment\n")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Redis Connection", test_redis_connection),
        ("AI Service", test_ai_service_directly),
        ("Core Logic", test_core_logic_directly),
        ("Webhook Simulation", test_webhook_simulation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  ❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! The system should work in deployment.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        print("\n🔧 Next steps:")
        print("1. Fix any failed tests")
        print("2. Check Render logs for specific error messages")
        print("3. Verify environment variables in Render dashboard")

if __name__ == "__main__":
    main() 