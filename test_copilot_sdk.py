"""
Test GitHub Copilot SDK Setup

This script validates the Copilot SDK installation and demonstrates basic usage.
"""

import asyncio
from copilot import CopilotClient

async def test_basic_agent():
    """Test basic Copilot SDK functionality"""
    
    print("🚀 Testing GitHub Copilot SDK...")
    print("=" * 60)
    
    client = None
    session = None
    
    try:
        # Initialize Copilot client
        print("\n1. Initializing Copilot client...")
        
        # Explicitly specify CLI path on Windows if needed, but uv should handle it
        # cli_path = r"C:\Users\djgia\AppData\Roaming\npm\copilot.cmd"
        
        client = CopilotClient()
        print("   ✅ Client initialized")
        
        # Start the client
        print("\n2. Starting client...")
        await client.start()
        print("   ✅ Client started successfully")
        
        # Create a session
        print("\n3. Creating agent session...")
        session = await client.create_session({
            "model": "gpt-4",  # Can also use "claude-sonnet-4.5", etc.
        })
        
        print("   ✅ Session created successfully")
        
        # Send a simple prompt to test
        print("\n4. Testing agent with simple prompt...")
        prompt = """
        You are a data engineering assistant. 
        
        Given this sample mapping:
        - Source column: "CUSTOMER_NAME" → Target column: "CLIENT_NAME"
        - Source column: "ACCT_NUMBER" → Target column: "ACCOUNT_ID"
        
        Generate a brief pseudocode description of how to transform this data.
        Keep it to 3-4 lines.
        """
        
        print("   ⏳ Waiting for AI response...")
        result_event = await session.send_and_wait({"prompt": prompt})

        # The assistant's final message is in the event preceding the ASSISTANT_TURN_END event
        if result_event and result_event.parent_id:
            final_message_event = session.get_event(result_event.parent_id)
            if final_message_event and final_message_event.type == SessionEventType.ASSISTANT_MESSAGE:
                assistant_response = final_message_event.data.content
                print("\n   ✅ Agent Response:")
                print("   " + "-" * 56)
                # Indent the response for readability
                for line in assistant_response.split('\n'):
                    print(f"     {line}")
                print("   " + "-" * 56)
        
        # Cleanup
        print("\n5. Cleaning up...")
        await session.destroy()
        await client.stop()
        print("   ✅ Cleanup complete")
        
        print("\n✅ Copilot SDK test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nError type: {type(e).__name__}")
        
        # Try to cleanup
        try:
            if session:
                await session.destroy()
            if client:
                await client.stop()
        except:
            pass
        
        import traceback
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    print("GitHub Copilot SDK - Initial Test")
    print("=" * 60)
    
    success = asyncio.run(test_basic_agent())
    
    if success:
        print("\n🎉 Ready to build our data engineering agent!")
    else:
        print("\n📚 Next step: Configure authentication or check CLI path")

