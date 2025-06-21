import os
import sqlite3
import json
import networkx as nx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import subprocess
import requests
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import re
import xml.etree.ElementTree as ET

app = FastAPI(
    title="SHADOW CHAMELEON API",
    description="AI Red Team Partner that evolves with every engagement",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure your Shodan API key here
SHODAN_API_KEY = "85jh0HrXYrT5ojwhkAdWX3fozMe9s5jK"

# Database setup
def init_db():
    conn = sqlite3.connect('shadow_chameleon.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS engagements
                 (id TEXT PRIMARY KEY,
                  target TEXT,
                  timestamp DATETIME,
                  tech_stack TEXT,
                  attack_graph TEXT,
                  results TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS playbooks
                 (id TEXT PRIMARY KEY,
                  name TEXT,
                  tech_pattern TEXT,
                  commands TEXT,
                  effectiveness REAL)''')
    
    # Insert fixed sample playbooks
    c.execute("SELECT COUNT(*) FROM playbooks")
    if c.fetchone()[0] == 0:
        sample_playbooks = [
            ("wordpress_exploit", "WordPress Plugin Exploit", "wordpress", 
             "wpscan --url {target} --enumerate vp; searchsploit {plugin}", 0.85),
            ("jenkins_rce", "Jenkins RCE", "jenkins", 
             "nmap -sV {target}; searchsploit jenkins", 0.78),
            ("ssh_bruteforce", "SSH Bruteforce", "openssh", 
             "hydra -l {user} -P {wordlist} ssh://{target} -t 4 -vV", 0.65),
            ("http_recon", "HTTP Server Recon", "http", 
             "nmap -sV -p {port} {target}; curl -I {target}:{port}", 0.7)
        ]
        
        for pb in sample_playbooks:
            c.execute("INSERT INTO playbooks VALUES (?, ?, ?, ?, ?)",
                     (pb[0], pb[1], pb[2], pb[3], pb[4]))
    
    conn.commit()
    conn.close()

init_db()

# Data models
class TargetRequest(BaseModel):
    target: str
    scan_depth: Optional[str] = "normal"

class PlaybookRecommendation(BaseModel):
    playbook_id: str
    name: str
    confidence: float
    commands: List[str]
    visualization: Optional[str] = None

class EngagementResult(BaseModel):
    success: bool
    output: str
    learned_patterns: Optional[Dict] = None

# OSINT gathering functions
def run_nmap(target: str) -> Dict:
    try:
        result = subprocess.run(
            ["nmap", "-sV", "-oX", "-", target],
            capture_output=True,
            text=True,
            check=True
        )
        return parse_nmap_xml(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"error": f"Nmap scan failed: {e.stderr}"}

def parse_nmap_xml(xml: str) -> Dict:
    try:
        root = ET.fromstring(xml)
        services = []
        
        for host in root.findall('host'):
            # Extract host address
            address = host.find("address").get("addr") if host.find("address") is not None else ""
            
            for ports in host.findall('ports'):
                for port in ports.findall('port'):
                    portid = port.get('portid')
                    protocol = port.get('protocol')
                    
                    service = port.find('service')
                    service_name = service.get('name', '') if service is not None else ''
                    product = service.get('product', '') if service is not None else ''
                    version = service.get('version', '') if service is not None else ''
                    
                    services.append({
                        "port": portid,
                        "protocol": protocol,
                        "name": service_name,
                        "product": product,
                        "version": version
                    })
        
        return {"services": services}
    except ET.ParseError as e:
        return {"error": f"XML parsing failed: {str(e)}", "services": []}

def query_shodan(target: str) -> Dict:
    try:
        if not SHODAN_API_KEY or SHODAN_API_KEY == "YOUR_SHODAN_API_KEY":
            return {"error": "Shodan API key not configured"}
        
        response = requests.get(
            f"https://api.shodan.io/shodan/host/{target}?key={SHODAN_API_KEY}",
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Attack graph generation
def build_attack_graph(tech_stack: Dict) -> nx.DiGraph:
    G = nx.DiGraph()
    
    for service in tech_stack.get("services", []):
        node_id = f"{service['name']}:{service['port']}"
        G.add_node(node_id, type="service", **service)
    
    # Add vulnerability nodes based on common patterns
    if any("http" in s.get("name", "").lower() for s in tech_stack.get("services", [])):
        G.add_node("web_vulns", type="vulnerability", name="Web Application Vulns")
        for node in G.nodes():
            if "http" in node.lower():
                G.add_edge(node, "web_vulns", weight=0.7)
    
    if any("ssh" in s.get("name", "").lower() for s in tech_stack.get("services", [])):
        G.add_node("ssh_weak_creds", type="vulnerability", name="SSH Weak Credentials")
        for node in G.nodes():
            if "ssh" in node.lower():
                G.add_edge(node, "ssh_weak_creds", weight=0.6)
    
    return G

def visualize_graph(G: nx.DiGraph) -> str:
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G)
    
    service_nodes = [n for n, attr in G.nodes(data=True) if attr["type"] == "service"]
    vuln_nodes = [n for n, attr in G.nodes(data=True) if attr["type"] == "vulnerability"]
    
    nx.draw_networkx_nodes(G, pos, nodelist=service_nodes, node_color="skyblue", node_size=2000)
    nx.draw_networkx_nodes(G, pos, nodelist=vuln_nodes, node_color="lightcoral", node_size=2000)
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)
    nx.draw_networkx_labels(G, pos, font_size=10)
    
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# Playbook recommendation engine
def recommend_playbooks(tech_stack: Dict, G: nx.DiGraph) -> List[PlaybookRecommendation]:
    conn = sqlite3.connect('shadow_chameleon.db')
    c = conn.cursor()
    c.execute("SELECT * FROM playbooks")
    playbooks = c.fetchall()
    conn.close()
    
    recommendations = []
    
    for pb in playbooks:
        pb_id, name, pattern, commands, effectiveness = pb
        
        # Check if pattern exists in any service
        pattern_found = False
        for service in tech_stack.get("services", []):
            service_name = service.get("name", "").lower()
            service_product = service.get("product", "").lower()
            
            if pattern.lower() in service_name or pattern.lower() in service_product:
                pattern_found = True
                break
        
        if pattern_found:
            confidence = effectiveness * 0.9
            formatted_commands = []
            
            for cmd in commands.split(";"):
                cmd = cmd.strip()
                cmd = cmd.replace("{target}", tech_stack.get("target", ""))
                
                # Add service-specific replacements
                for service in tech_stack.get("services", []):
                    service_name = service.get("name", "").lower()
                    service_product = service.get("product", "").lower()
                    
                    if pattern.lower() in service_name or pattern.lower() in service_product:
                        cmd = cmd.replace("{port}", service["port"])
                        if "{plugin}" in cmd and service.get("product"):
                            cmd = cmd.replace("{plugin}", service["product"])
                
                formatted_commands.append(cmd)
            
            try:
                vis = visualize_graph(G)
            except Exception as e:
                print(f"Visualization failed: {str(e)}")
                vis = None
                
            recommendations.append(PlaybookRecommendation(
                playbook_id=pb_id,
                name=name,
                confidence=round(confidence, 2),
                commands=formatted_commands,
                visualization=vis
            ))
    
    recommendations.sort(key=lambda x: x.confidence, reverse=True)
    return recommendations

# API Endpoints
@app.post("/analyze", response_model=List[PlaybookRecommendation])
async def analyze_target(request: TargetRequest):
    # Validate target
    if not re.match(r'^[\w\.-]+$', request.target):
        raise HTTPException(status_code=400, detail="Invalid target format")
    
    # Gather OSINT data
    nmap_results = run_nmap(request.target)
    shodan_results = query_shodan(request.target)
    
    tech_stack = {
        "target": request.target,
        "services": nmap_results.get("services", []),
        "shodan": shodan_results
    }
    
    # Build attack graph
    try:
        attack_graph = build_attack_graph(tech_stack)
    except Exception as e:
        print(f"Attack graph generation failed: {str(e)}")
        attack_graph = nx.DiGraph()
    
    # Recommend playbooks
    recommendations = recommend_playbooks(tech_stack, attack_graph)
    
    # Save engagement to DB
    conn = sqlite3.connect('shadow_chameleon.db')
    c = conn.cursor()
    engagement_id = f"eng_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    c.execute("INSERT INTO engagements VALUES (?, ?, ?, ?, ?, ?)",
             (engagement_id,
              request.target,
              datetime.now().isoformat(),
              json.dumps(tech_stack),
              json.dumps(nx.node_link_data(attack_graph)),
              json.dumps([r.dict() for r in recommendations])))
    
    conn.commit()
    conn.close()
    
    return recommendations

@app.post("/execute/{playbook_id}", response_model=EngagementResult)
async def execute_playbook(playbook_id: str, commands: List[str]):
    # Security check - only allow safe commands
    allowed_tools = ["nmap", "wpscan", "searchsploit", "hydra", "curl", "whois"]
    sanitized_commands = []
    
    for cmd in commands:
        cmd_lower = cmd.lower()
        if not any(tool in cmd_lower for tool in allowed_tools):
            raise HTTPException(
                status_code=400, 
                detail=f"Command not allowed: {cmd.split()[0]}"
            )
        sanitized_commands.append(cmd)
    
    results = []
    
    for cmd in sanitized_commands:
        try:
            # Execute command with timeout
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            results.append({
                "command": cmd,
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            })
        except subprocess.TimeoutExpired as e:
            results.append({
                "command": cmd,
                "success": False,
                "output": "",
                "error": f"Command timed out (300s): {str(e)}"
            })
        except Exception as e:
            results.append({
                "command": cmd,
                "success": False,
                "output": "",
                "error": f"Execution failed: {str(e)}"
            })
    
    # Simple learning - in production use ML
    learned = {}
    if any("wordpress" in cmd.lower() for cmd in sanitized_commands):
        learned["wordpress_pattern"] = "WordPress vulnerabilities found"
    elif any("ssh" in cmd.lower() for cmd in sanitized_commands):
        learned["ssh_pattern"] = "SSH brute force attempted"
    elif any("http" in cmd.lower() for cmd in sanitized_commands):
        learned["http_pattern"] = "HTTP reconnaissance performed"
    
    return EngagementResult(
        success=all(r["success"] for r in results),
        output=json.dumps(results, indent=2),
        learned_patterns=learned
    )


@app.get("/engagements")
async def get_engagements(limit: int = 10):
    conn = sqlite3.connect('shadow_chameleon.db')
    c = conn.cursor()
    c.execute("SELECT * FROM engagements ORDER BY timestamp DESC LIMIT ?", (limit,))
    engagements = c.fetchall()
    conn.close()
    
    return [{
        "id": e[0],
        "target": e[1],
        "timestamp": e[2],
        "tech_stack": json.loads(e[3]),
        "attack_graph": json.loads(e[4]),
        "results": json.loads(e[5])
    } for e in engagements]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
