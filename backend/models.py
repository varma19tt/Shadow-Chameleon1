from sqlite3 import Connection
from typing import TypedDict

class Service(TypedDict):
    name: str
    port: str
    product: str
    version: str

class Playbook(TypedDict):
    id: str
    name: str
    description: str
    tech_pattern: str
    commands: str
    effectiveness: float

def init_db(conn: Connection):
    conn.execute('''CREATE TABLE IF NOT EXISTS engagements
                 (id TEXT PRIMARY KEY, target TEXT, timestamp DATETIME,
                  tech_stack TEXT, attack_graph TEXT, results TEXT)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS playbooks
                 (id TEXT PRIMARY KEY, name TEXT, description TEXT,
                  tech_pattern TEXT, commands TEXT, effectiveness REAL)''')
