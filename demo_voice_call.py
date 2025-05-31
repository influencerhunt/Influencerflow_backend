"""
Demo script to test the voice call functionality with negotiation agent.
"""

import asyncio
import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
NGROK_URL = "https://74f4-2405-201-c405-187d-9445-fd82-f87c-e561.ngrok-free.app"  # Replace with your actual ngrok URL

async def demo_voice_call():
    """Demonstrate voice call functionality with negotiation agent."""
    
    print("🎯 Starting Voice Call Negotiation Demo\n")
    
    # Test data for voice call
    voice_call_data = {
        "to_number": "+919030930161",  # Replace with actual test number
        "webhook_base_url": NGROK_URL,
        "brand_details": {
            "name": "EcoTech Solutions",
            "budget": 8000.0,
            "goals": ["brand awareness", "product launch", "sustainability messaging"],
            "target_platforms": ["instagram", "youtube"],
            "content_requirements": {
                "instagram_post": 4,
                "instagram_reel": 3,
                "youtube_shorts": 2
            },
            "campaign_duration_days": 45,
            "target_audience": "Environmentally conscious millennials and Gen Z",
            "brand_guidelines": "Authentic content showcasing sustainability and innovation"
        },
        "influencer_profile": {
            "name": "Sarah EcoLiving",
            "followers": 125000,
            "engagement_rate": 0.078,
            "location": "US",
            "platforms": ["instagram", "youtube"],
            "niches": ["sustainability", "zero waste", "green technology"],
            "previous_brand_collaborations": 25
        }
    }
    
    print("📞 Starting voice call with negotiation capabilities...")
    print(f"Brand: {voice_call_data['brand_details']['name']}")
    print(f"Budget: ${voice_call_data['brand_details']['budget']:,.2f}")
    print(f"Target: {voice_call_data['influencer_profile']['name']}")
    print(f"Platforms: {', '.join(voice_call_data['brand_details']['target_platforms'])}")
    print(f"To Number: {voice_call_data['to_number']}")
    print()
    
    try:
        # Start voice call
        response = requests.post(
            f"{BASE_URL}/api/v1/negotiation-fixed/voice/start-call",
            json=voice_call_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Voice call initiated successfully!")
            print(f"📞 Call SID: {result['call_sid']}")
            print(f"🆔 Negotiation Session ID: {result['negotiation_session_id']}")
            print(f"📝 Initial Message: {result['initial_negotiation_message'][:200]}...")
            print()
            
            call_sid = result['call_sid']
            
            # Monitor call status
            print("📊 Monitoring call status...")
            for i in range(3):
                status_response = requests.get(
                    f"{BASE_URL}/api/v1/negotiation-fixed/voice/status/{call_sid}"
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Status Check {i+1}: {status_data['call_status']}")
                    
                    if status_data.get('negotiation_summary'):
                        summary = status_data['negotiation_summary']
                        print(f"  📋 Negotiation Status: {summary['status']}")
                        print(f"  🔄 Round: {summary['negotiation_round']}")
                        print(f"  💬 Messages: {summary['conversation_length']}")
                
                time.sleep(2)
            
            print()
            
            # List all voice sessions
            sessions_response = requests.get(
                f"{BASE_URL}/api/v1/negotiation-fixed/voice/sessions"
            )
            
            if sessions_response.status_code == 200:
                sessions_data = sessions_response.json()
                print(f"📱 Active Voice Calls: {sessions_data['active_voice_calls']}")
                
                for call in sessions_data['calls']:
                    print(f"  • Call {call['call_sid'][:12]}... - {call['status']}")
                    print(f"    Brand: {call['brand_name']}, Influencer: {call['influencer_name']}")
            
            print()
            
            # Test mock voice call for demonstration
            print("🧪 Testing mock voice call...")
            mock_response = requests.post(
                f"{BASE_URL}/api/v1/negotiation-fixed/test/mock-voice-call"
            )
            
            if mock_response.status_code == 200:
                mock_result = mock_response.json()
                print("✅ Mock voice call created successfully!")
                print(f"📞 Mock Call SID: {mock_result['call_sid']}")
                print(f"🎯 Message: {mock_result['message']}")
            
            print()
            print("🎉 Voice call demo completed!")
            print()
            print("💡 Next steps:")
            print("1. Set up ngrok: ngrok http 8000")
            print("2. Update NGROK_URL in this script with your ngrok URL")
            print("3. Configure Twilio webhook URLs to point to your ngrok URL")
            print("4. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER in .env")
            print("5. Replace +1234567890 with a real phone number for testing")
            
        else:
            print(f"❌ Failed to start voice call: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the FastAPI server is running!")
        print("Run: uvicorn main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_webhook_endpoints():
    """Test webhook endpoints (for manual testing)."""
    
    print("\n🔗 Testing Webhook Endpoints")
    print("=" * 50)
    
    # Test endpoints that would be called by Twilio
    webhook_endpoints = [
        "/api/v1/negotiation-fixed/voice/inbound",
        "/api/v1/negotiation-fixed/voice/gather", 
        "/api/v1/negotiation-fixed/voice/partial"
    ]
    
    print("Available webhook endpoints:")
    for endpoint in webhook_endpoints:
        print(f"  • POST {BASE_URL}{endpoint}")
    
    print("\nTwilio Configuration:")
    print(f"  Voice URL: {NGROK_URL}/api/v1/negotiation-fixed/voice/inbound")
    print(f"  Voice Method: POST")
    print(f"  Status Callback URL: (optional)")

def test_api_endpoints():
    """Test all available API endpoints."""
    
    print("\n🔧 Available API Endpoints")
    print("=" * 50)
    
    endpoints = [
        ("POST", "/api/v1/negotiation-fixed/voice/start-call", "Start voice call"),
        ("GET", "/api/v1/negotiation-fixed/voice/status/{call_sid}", "Get call status"),
        ("GET", "/api/v1/negotiation-fixed/voice/sessions", "List voice sessions"),
        ("DELETE", "/api/v1/negotiation-fixed/voice/end-session/{call_sid}", "End voice session"),
        ("POST", "/api/v1/negotiation-fixed/test/mock-voice-call", "Test mock voice call"),
        ("POST", "/api/v1/negotiation-fixed/start", "Start text negotiation"),
        ("POST", "/api/v1/negotiation-fixed/continue", "Continue text negotiation"),
        ("GET", "/api/v1/negotiation-fixed/sessions", "List negotiation sessions"),
    ]
    
    for method, endpoint, description in endpoints:
        print(f"  {method:6} {BASE_URL}{endpoint}")
        print(f"         {description}")
        print()

if __name__ == "__main__":
    print("🚀 Voice Call Negotiation Agent Demo")
    print("=" * 60)
    
    # Check if FastAPI server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ FastAPI server is running")
        else:
            print("⚠️  Server responded but may have issues")
    except:
        print("❌ FastAPI server is not running!")
        print("Please start it with: uvicorn main:app --reload")
        exit(1)
    
    # Check environment variables
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY not set - agent will run in mock mode")
    
    if not all([
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN"), 
        os.getenv("TWILIO_NUMBER")
    ]):
        print("⚠️  Warning: Twilio credentials not set - voice calls will run in mock mode")
    
    print()
    
    # Run the demo
    asyncio.run(demo_voice_call())
    
    # Show additional information
    test_webhook_endpoints()
    test_api_endpoints()
    
    print("\n📚 For more details, visit: http://localhost:8000/docs") 