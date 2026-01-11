"""
Hub Manager Module.
Strictly manages synchronization between Local code and LangSmith Hub.
Enforces "No Failover" policy: If a prompt cannot be retrieved or created in the Hub, the system MUST fail.
"""
import os
import logging
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

# Load Env Forcefully
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logger = logging.getLogger("HubManager")

def get_or_push_prompt(repo_name: str, default_content: str) -> str:
    """
    Retrieves a prompt from LangSmith Hub.
    If it does not exist, PUSHES the local default to create it.
    If it fails to connect or sync, RAISES an exception (No failover to local silent).
    
    Args:
        repo_name: The simple name of the repo (e.g., "director-system-main").
        default_content: The local system prompt string to use as the source of truth if Hub is empty.
        
    Returns:
        The prompt template string (content of the System Message).
    """
    handle = os.getenv("LANGCHAIN_HUB_HANDLE")
    if not handle:
        raise ValueError("CRITICAL: LANGCHAIN_HUB_HANDLE is not set in .env. Cannot sync with LangSmith Hub.")

    full_repo = f"{handle}/{repo_name}"
    client = Client()
    
    try:
        logger.info(f"📡 Attempting to Pull Prompt: {full_repo}")
        prompt_obj = client.pull_prompt(full_repo)
        
        # Extract System Message Content from ChatPromptTemplate
        # Expected Structure: ChatPromptTemplate(messages=[SystemMessagePromptTemplate(prompt=PromptTemplate(template='...')), ...])
        
        if hasattr(prompt_obj, "messages") and len(prompt_obj.messages) > 0:
             first_msg = prompt_obj.messages[0]
             
             # Case A: SystemMessagePromptTemplate
             if hasattr(first_msg, "prompt") and hasattr(first_msg.prompt, "template"):
                 return first_msg.prompt.template
                 
             # Case B: Direct Message (unlikely for Hub pull but possible)
             if hasattr(first_msg, "content"):
                 return first_msg.content
        
        # Fallback: If we can't parse it but pulled it, wait... strict mode?
        # If we can't understand the format, we can't use it as a 'system_prompt' string.
        # But maybe we can just return the default if parsing fails? 
        # User said "No failover to local".
        # So we must raise error or fix parsing.
        
        # Let's assume standard push/pull structure.
        # If it fails to parse, we might be getting a weird object.
        logger.warning(f"⚠️ Prompt retrieved but structure unclear. Type: {type(prompt_obj)}")
        # Try converting to string representation or check input_variables
        raise ValueError(f"Retrieved prompt {full_repo} does not match expected System Message format.")

    except Exception as e:
        # Check if it is a 404 / Not Found
        error_str = str(e).lower()
        # '404' or 'not found' is typical SDK response for missing repo
        if "404" in error_str or "not found" in error_str:
            logger.warning(f"⚠️ Prompt {full_repo} not found in Hub. PUSHING Local Default...")
            try:
                # Push the default as a clean ChatPromptTemplate
                prompt = ChatPromptTemplate.from_messages([
                    ("system", default_content),
                    ("placeholder", "{messages}")
                ])
                
                # Attempt Push
                try:
                    url = client.push_prompt(full_repo, object=prompt)
                except Exception as tenant_error:
                    # Check for Tenant Mismatch (User put wrong handle in .env)
                    if "another tenant" in str(tenant_error) or "Current tenant" in str(tenant_error):
                        logger.warning(f"⚠️ Handle mismatch ('{handle}'). Pushing to default authenticated tenant...")
                        # Push to simple name, let SDK resolve the handle
                        # Note: This means 'full_repo' variable is technically wrong for the return log, but the URL will be right.
                        url = client.push_prompt(repo_name, object=prompt)
                    else:
                        raise tenant_error
                        
                logger.info(f"✅ Successfully Pushed: {url}")
                
                # Update: Since we just pushed, we can trust the default content matches.
                return default_content
                
            except Exception as push_error:
                # SPECIAL CASE: 409 Conflict "Nothing to commit"
                # This happens if we tried to push, but the content is actually identical to what's already there.
                # This implies state is actually valid/synced.
                if "409" in str(push_error) and "Nothing to commit" in str(push_error):
                    logger.info("ℹ️ Prompt already exists and is up to date (No changes detected).")
                    return default_content
                    
                raise RuntimeError(f"🔥 CRITICAL FAILURE: Could not PUSH prompt to Hub: {push_error}") from push_error
        else:
            # Genuine Connection/Auth Error -> Strict Fail
            raise RuntimeError(f"🔥 CRITICAL FAILURE: Could not PULL prompt from Hub: {e}") from e
