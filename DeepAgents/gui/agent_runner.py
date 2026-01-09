import concurrent.futures
import sys
import os
import io
import contextlib

# Import Agents directly creates dependency issues if we not careful with paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from DeepAgents.CommercialAgents.director_agent.agent import create_director_agent
from DeepAgents.CommercialAgents.research_agent.agent import create_research_agent, run_research_task
from DeepAgents.CommercialAgents.confidence_agent.agent import create_confidence_agent
from DeepAgents.CommercialAgents.composer_agent.agent import create_composer_agent
from DeepAgents.CommercialAgents.cinematographer_agent.agent import create_cinematographer_agent
from DeepAgents.agent_brain import AgentConfig, AgentMemory

class AgentRunner:
    def __init__(self, session_manager):
        self.session = session_manager
        self.config = AgentConfig() # Load config
        self.brain = AgentMemory() # Load memory for Composer
        
    def stream_director(self, directive):
        """Runs director and streams events to the session log."""
        
        # Load Config for Director
        dir_conf = self.config.get_agent_config("Director")
        provider = dir_conf["provider"]
        model = dir_conf["model"]
        
        self.session.log_event("Director", "info", f"Starting directive: {directive} (Provider: {provider}, Model: {model})")
        
        try:
            # Pass provider and model to factory
            agent = create_director_agent(provider=provider, model_name=model)
            
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
            
            for event in agent.stream(
                {"messages": [("user", directive)]}, 
                config=config # type: ignore
            ):
                # Standard LangGraph parsing logic (similar to what I verified in agent.py)
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
                        
                        # 1. Log Output
                        if hasattr(msg, "content") and msg.content:
                             self.session.log_event("Director", "output", msg.content)
                             yield ("Director", "output", msg.content)

                        # 2. Log Tool Calls
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                             for tc in msg.tool_calls:
                                 log_entry = f"Calling Tool: {tc['name']} with args {tc['args']}"
                                 self.session.log_event("Director", "thinking", log_entry, tool_calls=tc)
                                 yield ("Director", "thinking", log_entry)
                                 
                                 # Special Case: If calling Research Agent, spawn a sub-logger
                                 if tc['name'] == 'consult_research_agent':
                                     topic = tc['args'].get('topic')
                                     yield ("System", "info", f"Triggering Research Agent for: {topic}")
                                     # Note: The tool execution happens inside the graph, so we capture the result in the next step
                                     
        except Exception as e:
            self.session.log_event("Director", "error", str(e))
            yield ("Director", "error", str(e))

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
