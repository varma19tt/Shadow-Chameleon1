import os

class Config:
    SHODAN_API_KEY = os.getenv("SHODAN_API_KEY", "85jh0HrXYrT5ojwhkAdWX3fozMe9s5jK")
    DATABASE_URL = "sqlite:///shadow_chameleon.db"
    MAX_SCAN_DURATION = 300  # seconds
