import os
import json
import datetime
import glob

HISTORY_DIR = os.path.join(os.path.dirname(__file__), "history")
os.makedirs(HISTORY_DIR, exist_ok=True)

class SessionManager:
    def __init__(self, session_id=None):
        if not session_id:
            self.session_id = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        else:
            self.session_id = session_id
            
        self.session_dir = os.path.join(HISTORY_DIR, self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        
        self.log_file = os.path.join(self.session_dir, "full_log.jsonl")

    def create_session(self, description=None):
        """Creates a new session directory and returns the ID."""
        new_id = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        new_dir = os.path.join(HISTORY_DIR, new_id)
        os.makedirs(new_dir, exist_ok=True)
        
        if description:
            try:
                with open(os.path.join(new_dir, "meta.json"), "w", encoding='utf-8') as f:
                    json.dump({"description": description, "created": new_id}, f)
            except Exception:
                pass
                
        return new_id

    def log_event(self, agent_name, event_type, content, tool_calls=None):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "agent": agent_name,
            "type": event_type, # 'thinking', 'tool', 'output', 'error'
            "content": str(content),
            "tool_calls": tool_calls or []
        }
        
        with open(self.log_file, "a", encoding='utf-8') as f:
            f.write(json.dumps(entry) + "\n")
            
        return entry

    def load_history(self):
        if not os.path.exists(self.log_file):
            return []
        
        logs = []
        with open(self.log_file, "r", encoding='utf-8') as f:
            for line in f:
                logs.append(json.loads(line))
        return logs

def list_sessions():
    sessions = []
    # Find all directories in history
    dirs = glob.glob(os.path.join(HISTORY_DIR, "*"))
    for d in dirs:
        if os.path.isdir(d):
            sessions.append(os.path.basename(d))
    return sorted(sessions, reverse=True)
