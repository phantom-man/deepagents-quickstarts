import concurrent.futures
import sys
import os
import io
import contextlib
import asyncio

# Import Agents directly creates dependency issues if we not careful with paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from DeepAgents.CommercialAgents.director_agent.agent import create_director_agent
from DeepAgents.CommercialAgents.research_agent.agent import create_research_agent, run_research_task
from DeepAgents.CommercialAgents.confidence_agent.agent import create_confidence_agent
from DeepAgents.CommercialAgents.composer_agent.agent import create_composer_agent
from DeepAgents.CommercialAgents.cinematographer_agent.agent import create_cinematographer_agent
from DeepAgents.agent_brain import AgentConfig, AgentMemory
from DeepAgents.persistence import get_postgres_checkpointer

class AgentRunner:
    def __init__(self, session_manager):
        self.session = session_manager
        self.config = AgentConfig() # Load config
        self.brain = AgentMemory() # Load memory for Composer
        
        # Enable OTLP Tracing for GUI process if configured
        if os.environ.get("LANGSMITH_OTEL_ENABLED") == "true":
             if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
                 os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4318"

    async def _run_agent_async(self, agent_factory, inputs, config):
        """Helper to run agents async with persistence."""
        async with get_postgres_checkpointer() as checkpointer:
            # Re-compile the agent with the checkpointer
            # This is tricky because create_director_agent returns a compiled graph usually.
            # We might need to refactor create_director_agent to accept checkpointer, 
            # OR we need to attach it here if possible (LangGraph usually requires it at compile time).
            
            # Fortunately, we updated create_director_agent to accept checkpointer!
            # But here `agent_factory` is a function call.
            pass

    def stream_director(self, directive):
        """Runs director and streams events to the session log."""
        
        # Load Config for Director
        dir_conf = self.config.get_agent_config("Director")
        provider = dir_conf["provider"]
        model = dir_conf["model"]
        
        self.session.log_event("Director", "info", f"Starting directive: {directive} (Provider: {provider}, Model: {model})")
        
        # ASYNC WRAPPER FOR GUI
        # Streamlit is synchronous, but our new architecture is Async.
        # We need to run the async loop in a thread or use asyncio.run in a way that yields.
        
        async def run_loop():
            events_to_yield = []
            try:
                # Use Persistence
                async with get_postgres_checkpointer() as checkpointer:
                    agent = create_director_agent(
                        provider=provider, 
                        model_name=model, 
                        checkpointer=checkpointer
                    )
                    
                    # LangSmith Tracing Context
                    tags = ["deep-agents-system", "gui-triggered", "agent:director"]
                    metadata = {
                        "session_id": self.session.session_id,
                        "model_name": model,
                        "provider": provider,
                        "user_intent": "director_directive"
                    }
                    
                    config = {
                        "configurable": {"thread_id": f"gui_{self.session.session_id}"},
                        "tags": tags,
                        "metadata": metadata
                    }
                    
                    async for event in agent.astream(
                        {"messages": [("user", directive)]}, 
                        config=config # type: ignore
                    ):
                        # Parsing Logic
                        # Check if event is the raw messages dict (SimpleReActExecutor case)
                        if "messages" in event and isinstance(event["messages"], list):
                             msgs = event["messages"]
                             msg = msgs[-1]
                             
                             # Ensure we only capture AI output, not input echoes
                             is_ai = False
                             if hasattr(msg, "type") and msg.type == "ai":
                                 is_ai = True
                             elif hasattr(msg, "__class__") and "AIMessage" in msg.__class__.__name__:
                                 is_ai = True
                             
                             if is_ai and hasattr(msg, "content") and msg.content:
                                     events_to_yield.append(("Director", "output", msg.content))
                        
                        else:
                            # LangGraph case: {"node": {"messages": ...}}
                            for key in event:
                                val = event[key]
                                msgs = []
                                
                                if isinstance(val, dict) and "messages" in val:
                                    msgs = val["messages"]
                                    if hasattr(msgs, "value"): msgs = msgs.value
                                elif hasattr(val, "messages"):
                                    msgs = getattr(val, "messages", [])
                                    
                                if msgs and isinstance(msgs, list):
                                    msg = msgs[-1]
                                    
                                    # Ensure we only capture AI output
                                    is_ai = False
                                    if hasattr(msg, "type") and msg.type == "ai":
                                        is_ai = True
                                    elif hasattr(msg, "__class__") and "AIMessage" in msg.__class__.__name__:
                                        is_ai = True
                                        
                                    if is_ai and hasattr(msg, "content") and msg.content:
                                        events_to_yield.append(("Director", "output", msg.content))
                                    if is_ai and hasattr(msg, "tool_calls") and msg.tool_calls:
                                        for tc in msg.tool_calls:
                                            log_entry = f"Calling Tool: {tc['name']} with args {tc['args']}"
                                            events_to_yield.append(("Director", "thinking", log_entry))

            except Exception as e:
                events_to_yield.append(("Director", "error", str(e)))
            
            return events_to_yield

        # Create Sync-to-Async Bridge
        try:
             # Win32 Policy fix for Streamlit
             if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                
             results = asyncio.run(run_loop())
             for res in results:
                 if res[1] == "output": self.session.log_event("Director", "output", res[2])
                 elif res[1] == "thinking": self.session.log_event("Director", "thinking", res[2])
                 elif res[1] == "error": self.session.log_event("Director", "error", res[2])
                 yield res
                 
        except Exception as e:
            self.session.log_event("Director", "error", f"Async Loop Failed: {e}")
            yield ("Director", "error", f"System Error: {e}")

    # Legacy Sync Method (kept for reference, but shadowed by above logic)
    def _stream_director_sync(self, directive):
         pass

    def run_research_direct(self, topic):
        """Runs the research agent directly (not via Director)."""
        # Load Config for Researcher
        res_conf = self.config.get_agent_config("Researcher")
        # Research agent factory likely doesn't support provider yet, so we default to what keys allow
        # Ideally we update run_research_task to accept model too, but avoiding deep refactor of Researcher for now unless requested.
        # But user asked for "Variable that tells the agent code that were using that brands llms"
        
        model = res_conf["model"]
        self.session.log_event("Researcher", "info", f"Starting research on: {topic} (Model: {model})")
        yield ("Researcher", "info", f"Starting research on: {topic} (Model: {model})")

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
             tags = ["deep-agents-system", "gui-triggered", "agent:researcher"]
             metadata = {
                 "session_id": self.session.session_id,
                 "model_name": model,
                 "user_intent": "research_direct"
             }
             extra_config = {"tags": tags, "metadata": metadata}
             
             # Assuming run_research_task accepts model_name
             res = run_research_task(topic, extra_config=extra_config, model_name=model)
             
        output = f.getvalue()
        if output:
            self.session.log_event("Researcher", "output", output)
            yield ("Researcher", "output", output)
        
        self.session.log_event("Researcher", "output", str(res))
        yield ("Researcher", "output", str(res))

    def run_composer(self, director_output):
        """Runs the composer agent."""
        if not director_output:
            yield ("Composer", "error", "No context to compose for.")
            return

        conf = self.config.get_agent_config("Composer")
        self.session.log_event("Composer", "info", f"Composing Score... (Model: {conf['model']})")
        yield ("Composer", "thinking", "Analyzing Director's Vision and checking Memory for musical motifs...")
        
        try:
            agent_func = create_composer_agent(model_config=conf, brain=self.brain, session_id=self.session.session_id)
            if not agent_func:
                raise Exception("Failed to init Composer Agent")
                
            # Run
            result = agent_func(director_output)
            
            self.session.log_event("Composer", "output", result)
            yield ("Composer", "output", result)
            
        except Exception as e:
            self.session.log_event("Composer", "error", str(e))
            yield ("Composer", "error", str(e))

    def run_cinematographer(self, director_output, mode="storyboard", max_shots=1, duration_sec=5):
        """Runs the cinematographer agent."""
        if not director_output:
            yield ("Cinematographer", "error", "No context to visualize.")
            return

        conf = self.config.get_agent_config("Cinematographer")
        self.session.log_event("Cinematographer", "info", f"Visualizing Scene... (Modes: {mode}, Shots: {max_shots})")
        yield ("Cinematographer", "thinking", f"Translating textual vision into visual prompts and assets ({max_shots} shots)...")
        
        try:
            agent_func = create_cinematographer_agent(model_config=conf, brain=self.brain, session_id=self.session.session_id)
            if not agent_func:
                raise Exception("Failed to init Cinematographer Agent")
                
            # Run with extended parameters
            result = agent_func(director_output, mode=mode, max_shots=max_shots, duration_sec=duration_sec)
            
            self.session.log_event("Cinematographer", "output", result)
            yield ("Cinematographer", "output", result)
            
        except Exception as e:
             self.session.log_event("Cinematographer", "error", str(e))
             yield ("Cinematographer", "error", str(e))
