from main import build_attack_graph, recommend_playbooks
import networkx as nx

def test_attack_graph_creation():
    tech_stack = {
        "services": [
            {"name": "http", "port": "80", "product": "Apache"},
            {"name": "ssh", "port": "22", "product": "OpenSSH"}
        ]
    }
    graph = build_attack_graph(tech_stack)
    assert isinstance(graph, nx.DiGraph)
    assert len(graph.nodes()) > 0
