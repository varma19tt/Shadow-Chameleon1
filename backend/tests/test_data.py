TEST_TECH_STACK = {
    "target": "testfire.net",
    "services": [
        {
            "name": "http",
            "port": "80",
            "product": "Apache",
            "version": "2.4.41"
        },
        {
            "name": "ssh",
            "port": "22",
            "product": "OpenSSH",
            "version": "7.9"
        }
    ]
}

TEST_PLAYBOOKS = [
    {
        "id": "http_exploit",
        "name": "HTTP Exploit",
        "tech_pattern": "apache",
        "commands": "nmap -sV {target}; searchsploit apache"
    }
]
