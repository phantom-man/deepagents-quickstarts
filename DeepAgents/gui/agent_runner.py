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

class AgentRunner:
    def __init__(self, session_manager):
        self.session = session_manager
        
    def stream_director(self, directive, model="gemini-2.0-flash-exp"):
        """Runs director and streams events to the session log."""
        self.session.log_event("Director", "info", f"Starting directive: {directive} (Model: {model})")
        
        try:
            agent = create_director_agent(model_name=model)
            # LangSmith Tracing Context
            tags = ["deep-agents-system", "gui-triggered", "agent:director"]
            metadata = {
                "session_id": self.session.session_id,
                "model_name": model,
                "user_intent": "director_directive"
            }
            
            config = {
                "configurable": {"thread_id": f"gui_{self.session.session_id}"},
                "tags": tags,
                "metadata": metadata
            }
            
            for event in agent.stream(
                {"messages": [("user", directive)]}, 
                config=config
            ):
                # Standard LangGraph parsing logic (similar to what I verified in agent.py)
                for key in event:
                    val = event[key]
                    msgs = []
                    
                    if isinstance(val, dict) and "messages" in val:
                        msgs = val["messages"]
                        if hasattr(msgs, "value"): msgs = msgs.value
                    elif hasattr(val, "messages"):
                        msgs = val.messages
                        
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

    def run_research_direct(self, topic, model="gemini-2.0-flash-exp"):
        """Runs the research agent directly (not via Director)."""
        self.session.log_event("Researcher", "info", f"Starting research on: {topic} (Model: {model})")
        yield ("Researcher", "info", f"Starting research on: {topic} (Model: {model})")

        # Capture stdout to see internal print statements from run_research_task
        # because run_research_task uses print(), not just yields
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
             # LangSmith Tracing Context
             tags = ["deep-agents-system", "gui-triggered", "agent:researcher"]
             metadata = {
                 "session_id": self.session.session_id,
                 "model_name": model,
                 "user_intent": "research_direct"
             }
             extra_config = {"tags": tags, "metadata": metadata}
             
             # We can't yield from inside the redirected context easily in real-time
             # for a simple implementation, we might just run it and dump the log
             res = run_research_task(topic, extra_config=extra_config, model_name=model)
             
        # Log the captured stdout
        logs = f.getvalue()
        self.session.log_event("Researcher", "thinking", logs)
        yield ("Researcher", "thinking", logs)
        
        if res:
             self.session.log_event("Researcher", "output", res)
             yield ("Researcher", "output", res)

    def run_confidence_audit(self, content):
        """Runs the confidence agent directly."""
        pass # Similar implementation
