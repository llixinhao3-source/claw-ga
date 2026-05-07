"""GenericAgent - AI conversation engine for desktop pet"""
import sys
import threading
import time
import queue
import re
from pathlib import Path

class GeneraticAgent:
    def __init__(self):
        self.running = False
        self.agent = None
        self._thread = None
        
        # Load mykey
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from mykey import MINIMAX_API_KEY
            self.api_key = MINIMAX_API_KEY
        except:
            self.api_key = None
            
    def run(self):
        if not self.api_key or self.api_key == "your-minimax-api-key-here":
            print("[GenericAgent] No valid API key configured")
            self.running = True  # Keep running in demo mode
            return
            
        try:
            from agent_loop import GeneraticAgentLoop
            self.agent = GeneraticAgentLoop(self.api_key)
            self.running = True
            self.agent.run()
        except Exception as e:
            print(f"[GenericAgent] Error: {e}")
            
    def put_task(self, text):
        if not self.agent:
            q = queue.Queue()
            q.put({"next": "GenericAgent not initialized. Please configure API key.", "source": "agent"})
            return q
            
        return self.agent.put_task(text)

class SimpleAgentLoop:
    """Simple agent loop for testing"""
    def __init__(self, api_key):
        self.api_key = api_key
        self.running = False
        
    def run(self):
        self.running = True
        print("[SimpleAgent] Running in demo mode")
        
    def put_task(self, text):
        q = queue.Queue()
        def respond():
            time.sleep(2)
            q.put({"next": f"Echo: {text}", "source": "user"})
        threading.Thread(target=respond, daemon=True).start()
        return q

# Register the simple loop for demo
sys.modules['agent_loop'] = type(sys)('agent_loop')
sys.modules['agent_loop'].GeneraticAgentLoop = SimpleAgentLoop
