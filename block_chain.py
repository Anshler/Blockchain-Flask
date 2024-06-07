import random
import yaml

import hashlib
import json
from typing import List, Dict, Set, Any
from urllib.parse import urlparse
import requests
import threading
import default.block_chain_default


# The 'actual' blockchain, it acquires all the nodes (urls) from one of the 'original' chain
class BlockChain(default.block_chain_default.BlockChain):
    def __init__(self):
        self.__chain: List[Dict] = []
        self.__current_transactions: List[Dict] = []
        self.__block_lock = threading.Lock()
        self.__first_block()  # Genesis block
        self.__seed_node = random.choice(  # Initialize known networks
            yaml.safe_load(
                open('known_nodes.yaml', 'r'))['nodes'])
        self.__nodes = set()

    def register_node(self, address) -> bool:
        """
        Add a new node with an address
        """
        with self.__block_lock:

            # Get all nodes from seed network
            print(f'http://{self.__seed_node}/nodes')
            request_node = requests.get(f'http://{self.__seed_node}/nodes')
            request_chain = requests.get(f'http://{self.__seed_node}/chain')
            if request_node.status_code == 200:
                self.__nodes = set(request_node.json()['nodes'])
                self.__chain = request_chain.json()['chain']
            else:
                return False

            # Check if new node already registered
            parsed_url = urlparse(address).netloc
            if parsed_url in self.__nodes:
                return False
            for node in self.__nodes:
                requests.post(f'http://{node}/nodes/register', json={'node': parsed_url})
            self.__nodes.add(parsed_url)
            return True