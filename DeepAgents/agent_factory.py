import logging
from typing import List, Any, Dict, TypedDict, Annotated, Sequence
import operator

from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

logger = logging.getLogger("DeepAgentFactory")

# --- Custom Graph for Replicate (No Tool Binding) ---

class AgentState(TypedDict):
    """The state of the agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]

def create_replicate_langgraph(model, tools, system_prompt, checkpointer=None):
    """
    Creates a LangGraph StateGraph that implements a ReAct loop manually.
    This is required for models (like basic Llama 3 via Replicate) that do not support
    native tool calling (bind_tools).
    """
    tool_map = {t.name: t for t in tools}
    
    # 1. Define Nodes
    def call_model(state: AgentState):
        messages = state['messages']
        
        # Format the history into a prompt string implicitly handled by the adapter 
        # but we need to ensure the System Prompt + Tool Desc is injected if it's the first turn
        
        # We assume the Replicate Adapter handles list[BaseMessage] -> String conversion
        # We just need to prepend instructions if they aren't there
        
        # For this graph, we inject system instructions as the first message if needed
        # OR we rely on the implementation below to format it.
        # Let's simplify: Pass the full state history to the model.
        
        # We need to construct the ReAct System Prompt dynamically
        tool_names = ", ".join(tool_map.keys())
        tool_desc = "\n".join([f"{t.name}: {t.description}" for t in tool_map.values()])
        
        react_instructions = f"""{system_prompt}

You have access to these tools:
{tool_desc}

FORMAT:
Thought: <reasoning>
Action: <tool_name>
Action Input: <input>
Observation: <result>
...
Final Answer: <answer>

Begin!"""
        
        # Prepend System Prompt to the messages list passed to the model (Temporary for this call)
        # We don't want to permanently add it to state.messages every time, leading to duplicates.
        # So we construct a temporary list.
        
        # Check if system message exists
        has_sys = any(isinstance(m, SystemMessage) for m in messages)
        input_msgs = list(messages)
        if not has_sys:
            input_msgs.insert(0, SystemMessage(content=react_instructions))
            
        response = model.invoke(input_msgs)
        return {"messages": [response]}

    def run_tools(state: AgentState):
        last_message = state['messages'][-1]
        content = last_message.content
        
        # Manual ReAct Parsing
        if "Action:" in content and "Action Input:" in content:
            try:
                # Naive Parsing (Robust enough for demos)
                # Find the LAST occurrence of Action/Input to handle potential chain-of-thought verbose logs
                lines = content.split('\n')
                action_line = next((l for l in reversed(lines) if 'Action:' in l), None)
                input_line = next((l for l in reversed(lines) if 'Action Input:' in l), None)
                
                if action_line and input_line:
                    action_name = action_line.split('Action:')[-1].strip()
                    action_input = input_line.split('Action Input:')[-1].strip()
                    
                    if action_name in tool_map:
                        tool_impl = tool_map[action_name]
                        result = tool_impl.invoke(action_input)
                        return {"messages": [HumanMessage(content=f"Observation: {str(result)}")]}
                    else:
                         return {"messages": [HumanMessage(content=f"Observation: Error: Tool '{action_name}' not found.")]}
            except Exception as e:
                return {"messages": [HumanMessage(content=f"Observation: Error parsing action: {e}")]}
        
        return {"messages": [HumanMessage(content="Observation: Could not parse Action.")]}

    # 2. Define Conditional Logic
    def should_continue(state: AgentState):
        last_message = state['messages'][-1]
        content = last_message.content
        
        if "Final Answer:" in content:
            return END
        elif "Action:" in content:
            return "tools"
        else:
            # If no action and no final message, usually means it's chatting or confused.
            # We can decide to END or assume it's a Final Answer.
            # For ReAct, typically if it doesn't output Action, it's done.
            return END

    # 3. Build Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", run_tools)
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    
    workflow.add_edge("tools", "agent")
    
    return workflow.compile(checkpointer=checkpointer)


# Try to import from the installed 'deepagents' package
try:
    from deepagents.graph import create_deep_agent as _lib_create_deep_agent
    HAS_DEEPAGENTS_LIB = True
except ImportError:
    HAS_DEEPAGENTS_LIB = False
    _lib_create_deep_agent = None

def create_deep_agent(model: BaseChatModel, tools: List[Any], system_prompt: str, checkpointer: Any = None) -> Any:
    """
    Factory to create a DeepAgent. 
    Prefers the installed 'deepagents' library implementation if available (for full middleware support).
    Falls back to a simple LangGraph prebuilt agent if not.
    
    Args:
        model: The LLM/ChatModel instance.
        tools: List of tools available to the agent.
        system_prompt: The system instructions (Ontology).
        checkpointer: Optional LangGraph checkpoint saver for persistence/time-travel.
        
    Returns:
        A compiled LangGraph runnable (or DeepAgent equivalent).
    """
    # Force fallback to test if deepagents lib is the cause of Schema validation error
    if HAS_DEEPAGENTS_LIB and _lib_create_deep_agent:
        # Check if the model supports binding tools. 
        # Replicate models generally DO NOT support bind_tools natively in LangChain.
        # If we passed a Replicate model, we should fallback to the legacy ReAct construction
        # or wrapping it manually, but 'deepagents' lib likely assumes native binding.
        
        # Heuristic: Check for 'ChatReplicate' class name or 'replicate' in module
        try:
             # Basic check if it is ChatReplicate
            is_replicate = "replicate" in str(type(model)).lower()
        except:
            is_replicate = False
            
        if not is_replicate:
            # Safe to use the optimized lib
            return _lib_create_deep_agent(
                model=model,
                tools=tools,
                system_prompt=system_prompt,
                name="deep_agent_instance",
                checkpointer=checkpointer
            )
        else:
            logger.info("Replicate Model detected. Bypassing 'deepagents' lib (native tool binding unsupported). Using Legacy ReAct fallback.")

    
    logger.warning("Falling back to simple create_react_agent (deepagents lib not found OR Replicate model used)")
    
    # --- HANDLING REPLICATE / NON-BIND_TOOLS MODELS ---
    # langgraph.prebuilt.create_react_agent EXPECTS the model to support bind_tools().
    # If using ChatReplicate, this will fail. We need to use the legacy ReAct chain logic 
    # but wrapped in a Runnable for consistency, OR use a simplified graph.
    
    # Ideally, we swap to a customized ReAct implementation for these "Dumb" models.
    # For this patch, we will assume standard create_react_agent (which might fail if model.bind_tools is missing).
    
    # WORKAROUND: If ChatReplicate, we try to use the ToolNode pattern but we must verify if model supports it.
    # Since ChatReplicate does NOT, we really should use the ReAct Agent from LangChain (Legacy) 
    # and wrap it as a Runnable.
    
    if "replicate" in str(type(model)).lower():
        # Fallback for Replicate (No Tool Call Support)
        logger.info("Replicate Model detected. Creating Custom LangGraph ReAct Agent.")
        return create_replicate_langgraph(model, tools, system_prompt, checkpointer)

    # Standard Path for OpenAI/Gemini
    return create_react_agent(model, tools, state_modifier=system_prompt, checkpointer=checkpointer)
