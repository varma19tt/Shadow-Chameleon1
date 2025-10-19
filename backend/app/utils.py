import subprocess
from typing import List, Dict

def run_command(command: str) -> Dict:
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def parse_tech_stack(data: Dict) -> Dict:
    simplified = {
        "target": data.get("target"),
        "services": []
    }
    for service in data.get("services", []):
        simplified["services"].append({
            "name": service.get("name"),
            "port": service.get("port"),
            "product": service.get("product", "")
        })
    return simplified
