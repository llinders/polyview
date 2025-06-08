import os
from dotenv import load_dotenv

load_dotenv()

from agents.search_agent import search_node_test

if __name__ == "__main__":
    search_node_test()