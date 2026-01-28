"""
DeepAgents System Diagnostics & Health Check.
Performs "Pre-Flight" checks on critical resources (Network, APIs, Disk)
to prevent runtime failures during production.
"""

import importlib.util
import logging
import os

import requests
from dotenv import load_dotenv

# from langchain_google_genai import ChatGoogleGenerativeAI # Deprecated
from langchain_core.messages import HumanMessage
from langchain_google_vertexai import ChatVertexAI

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SystemDiagnostics")


class SystemDiagnostics:
    """Performs pre-flight system checks."""

    def __init__(self):
        self.status = {
            "network": False,
            "google_vertex": False,
            "replicate": False,
            "disk_io": False,
            "dependencies": {},
        }
        self.report = []

    def log(self, message: str, level: str = "INFO"):
        """Logs a message to the internal report and standard logger."""
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
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "assets"
        )
        try:
            os.makedirs(base_dir, exist_ok=True)
            test_file = os.path.join(base_dir, "write_test.tmp")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("test")
            os.remove(test_file)
            self.status["disk_io"] = True
            self.log(f"✅ Disk Writable: {base_dir}")
            return True
        except Exception as e:
            self.log(f"❌ Disk Error ({base_dir}): {e}", "ERROR")
            return False

    def probe_anthropic(self) -> bool:
        """Probes Anthropic API for Liveness."""
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.log("ℹ️ Anthropic Key not found. Skipping Anthropic Probe.")
            return False

        self.log("🤖 Probing Anthropic API...")
        if os.environ.get("SKIP_PROBE", "false").lower() == "true":
            self.log("⚠️ Skipping Anthropic Probe (SKIP_PROBE=true).")
            return True

        try:
            from langchain_anthropic import ChatAnthropic

            llm = ChatAnthropic(model_name="claude-3-haiku-20240307", max_retries=1)
            llm.invoke("ping")
            self.log("✅ Anthropic API Online.")
            return True
        except Exception as e:
            self.log(f"❌ Anthropic Probe Failed: {e}", "ERROR")
            return False

    def probe_google_vertex(self) -> bool:
        """
        Probes Google Vertex AI for Liveness and Quota.
        """
        # Load Config loosely to check if we even care about Google
        import json

        is_primary = True
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "data", "agent_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    # If Director is NOT Google, Google is not Critical
                    if config.get("Director", {}).get("provider") != "Google":
                        is_primary = False
        except:
            pass

        self.log(
            f"🤖 Probing Google Vertex AI (Quota Check)... {'(Secondary)' if not is_primary else ''}"
        )

        # Optimization: Don't probe if user requested a Skip
        if os.environ.get("SKIP_PROBE", "false").lower() == "true":
            self.log(
                "⚠️ Skipping Google Vertex Probe (SKIP_PROBE=true). Assuming Online."
            )
            self.status["google_vertex"] = True
            return True

        # If Google is NOT primary, we can skip or be lenient
        if not is_primary and not os.environ.get("GOOGLE_CLOUD_PROJECT"):
            self.log("ℹ️ Google Project not set and not primary. Skipping.")
            return True

        # List of models to try in order of preference/cost
        # Minimizing this list to avoid triggering spam filters
        models_to_test = ["gemini-2.0-flash-exp"]

        success = False
        for model_name in models_to_test:
            try:
                llm = ChatVertexAI(
                    model=model_name,
                    temperature=0.0,
                    # project=project, # Vertex uses google-auth default or env
                    # location=location, # Auto-detect usually best, or use kwarg
                    max_retries=0,  # Do not retry 429s during a probe
                )
                # Simple "Hello" query
                self.log(f"   > Pinging model: {model_name}...")
                llm.invoke([HumanMessage(content="ping")])

                self.status["google_vertex"] = True
                self.log(f"✅ Google Vertex AI Online (Model: {model_name})")
                success = True
                break  # Stop on first success
            except Exception as e:
                self.log(f"⚠️ Quota Exceeded/Error for {model_name}: {e}")

        if not success:
            level = "ERROR" if is_primary else "WARNING"
            self.log("❌ Google Vertex Probe Failed.", level)
            # Only return False if it was Critical (Primary)
            return not is_primary
        return True

    def probe_replicate(self) -> bool:
        """Checks Replicate Token validity if present."""
        token = os.environ.get("REPLICATE_API_TOKEN")
        if not token:
            self.log(
                "ℹ️ Replicate Token not found (Audio generation will use fallback)."
            )
            return False

        self.log("🎵 Probing Replicate API...")
        try:
            # We assume if the package imports and token exists, we are good for a basic check.
            # Real quota check requires an API call.
            headers = {"Authorization": f"Token {token}"}
            resp = requests.get(
                "https://api.replicate.com/v1/account", headers=headers, timeout=5
            )

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
                    self.log(
                        f"   - {lib}: MISSING (Features will be limited)", "WARNING"
                    )
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
        # New Anthropic Probe
        anthropic = self.probe_anthropic()

        self.probe_replicate()

        print("---------------------------------------")

        # Hard Stop Conditions
        if not net:
            print("🛑 ABORT: No Network Connectivity.")
            return False
        if not disk:
            print("🛑 ABORT: Disk Failure (Cannot save assets).")
            return False

        # Determine Brain Health
        # If Anthropic is active, we rely on it.
        brain_ok = anthropic if os.environ.get("ANTHROPIC_API_KEY") else vertex

        if not brain_ok:
            print("🛑 ABORT: Primary Agent Brain (LLM) Offline.")
            choice = input("Proceed anyway? (System may crash) [y/N]: ")
            if choice.lower() != "y":
                return False

        print("✅ Systems Nominal (or warnings accepted). Starting Engine.\n")
        return True


if __name__ == "__main__":
    diag = SystemDiagnostics()
    diag.run_preflight_checks()
