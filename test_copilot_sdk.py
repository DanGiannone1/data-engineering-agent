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
        cli_path = r"C:\Users\djgia\AppData\Roaming\npm\copilot.cmd"
        
        client = CopilotClient({"cli_path": cli_path})
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
        
        assistant_messages = []
        def handle_event(event):
            if "ASSISTANT_MESSAGE" in str(event.type):
                if hasattr(event, 'data') and event.data and hasattr(event.data, 'content'):
                    assistant_messages.append(event.data.content)

        session.on(handle_event)
        
        print("   ⏳ Waiting for AI response...")
        await session.send({"prompt": prompt})
        await asyncio.sleep(5) # Give time for the events to be processed

        if assistant_messages:
            print("\n   ✅ Agent Response:")
            print("   " + "-" * 56)
            # The response might come in chunks, so join them
            full_response = "".join(assistant_messages)
            # Indent the response for readability
            for line in full_response.split('\n'):
                print(f"     {line}")
            print("   " + "-" * 56)
        else:
            print("\n   No response received from agent.")
        
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

