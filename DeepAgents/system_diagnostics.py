"""
DeepAgents System Diagnostics & Health Check.
Performs "Pre-Flight" checks on critical resources (Network, APIs, Disk)
to prevent runtime failures during production.
"""
import os
import sys
import time
import logging
import requests
import importlib.util
from typing import Dict, Any, List

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SystemDiagnostics")

class SystemDiagnostics:
    def __init__(self):
        self.status = {
            "network": False,
            "google_vertex": False,
            "replicate": False,
            "disk_io": False,
            "dependencies": {}
        }
        self.report = []

    def log(self, message: str, level: str = "INFO"):
        self.report.append(f"[{level}] {message}")
        if level == "ERROR":
            logger.error(message)
        else:
            logger.info(message)

    def check_network(self) -> bool:
        """Pings reliable hosts to verify internet connectivity."""
        self.log("📡 Checking Network Connectivity...")
        try:
            requests.get("https://www.google.com", timeout=5)
            self.status["network"] = True
            self.log("✅ Network Online.")
            return True
        except requests.RequestException as e:
            self.log(f"❌ Network Unreachable: {e}", "ERROR")
            return False

    def check_disk_permissions(self) -> bool:
        """Verifies read/write access to the data/assets directory."""
        self.log("💾 Checking Disk Permissions...")
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "assets")
        try:
            os.makedirs(base_dir, exist_ok=True)
            test_file = os.path.join(base_dir, "write_test.tmp")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            self.status["disk_io"] = True
            self.log(f"✅ Disk Writable: {base_dir}")
            return True
        except Exception as e:
            self.log(f"❌ Disk Error ({base_dir}): {e}", "ERROR")
            return False

    def probe_google_vertex(self) -> bool:
        """
        Probes Google Vertex AI for Liveness and Quota.
        Uses a lightweight model call to check if we are rate-limited.
        """
        self.log("🤖 Probing Google Vertex AI (Quota Check)...")
        from langchain_google_vertexai import ChatVertexAI
        from langchain_core.messages import HumanMessage

        # List of models to try in order of preference/cost
        models_to_test = ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"]
        
        for model_name in models_to_test:
            try:
                llm = ChatVertexAI(model=model_name, temperature=0.0)
                # Simple "Hello" query
                self.log(f"   > Pinging model: {model_name}...")
                llm.invoke([HumanMessage(content="ping")])
                
                self.status["google_vertex"] = True
                self.log(f"✅ Google Vertex AI Online (Model: {model_name})")
                return True
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Quota exceeded" in error_str:
                    self.log(f"⚠️ Quota Exceeded for {model_name}. Pausing recommended.", "WARNING")
                elif "404" in error_str:
                     self.log(f"⚠️ Model {model_name} not found/available.", "WARNING")
                else:
                    self.log(f"❌ Probe Failed for {model_name}: {e}", "ERROR")

        self.log("❌ All Google Models Failed Probe.", "ERROR")
        return False

    def probe_replicate(self) -> bool:
        """Checks Replicate Token validity if present."""
        token = os.environ.get("REPLICATE_API_TOKEN")
        if not token:
            self.log("ℹ️ Replicate Token not found (Audio generation will use fallback).")
            return False
            
        self.log("🎵 Probing Replicate API...")
        try:
            # We assume if the package imports and token exists, we are good for a basic check.
            # Real quota check requires an API call.
            headers = {"Authorization": f"Token {token}"}
            resp = requests.get("https://api.replicate.com/v1/account", headers=headers, timeout=5)
            
            if resp.status_code == 200:
                self.log("✅ Replicate API Valid.")
                self.status["replicate"] = True
                return True
            elif resp.status_code == 401:
                self.log("❌ Replicate Token Invalid.", "ERROR")
                return False
            else:
               self.log(f"⚠️ Replicate Check status: {resp.status_code}", "WARNING")
               return False
        except Exception as e:
             self.log(f"❌ Replicate Probe Error: {e}", "ERROR")
             return False

    def check_dependencies(self):
        """Checks for optional but important libraries."""
        self.log("📦 Checking Dependencies...")
        
        libs = ["moviepy", "langchain", "lancedb"]
        for lib in libs:
            try:
                if importlib.util.find_spec(lib) is not None:
                    self.status["dependencies"][lib] = True
                    self.log(f"   - {lib}: Installed")
                else:
                    self.status["dependencies"][lib] = False
                    self.log(f"   - {lib}: MISSING (Features will be limited)", "WARNING")
            except Exception:
                 self.status["dependencies"][lib] = False

    def run_preflight_checks(self) -> bool:
        """Runs all checks. Returns True if Critical Systems are Go."""
        print("\n🛠️ --- SYSTEM PRE-FLIGHT DIAGNOSTICS ---")
        
        net = self.check_network()
        disk = self.check_disk_permissions()
        
        # Dependency check is non-fatal
        self.check_dependencies()
        
        # API Checks
        vertex = self.probe_google_vertex()
        self.probe_replicate()

        print("---------------------------------------")
        
        # Hard Stop Conditions
        if not net:
            print("🛑 ABORT: No Network Connectivity.")
            return False
        if not disk:
            print("🛑 ABORT: Disk Failure (Cannot save assets).")
            return False
        if not vertex:
            print("🛑 ABORT: Google Vertex AI Offline/Quota Exceeeded.")
            choice = input("Proceed anyway? (System may crash) [y/N]: ")
            if choice.lower() != 'y':
                return False

        print("✅ Systems Nominal (or warnings accepted). Starting Engine.\n")
        return True

if __name__ == "__main__":
    diag = SystemDiagnostics()
    diag.run_preflight_checks()
