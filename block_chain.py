import random
import yaml
import requests
import default.block_chain_default
from urllib.parse import urlparse


# The 'actual' blockchain, it acquires all the nodes (urls) from one of the 'default' chain
class BlockChain(default.block_chain_default.BlockChain):
    def __init__(self):
        super().__init__()
        self.__seed_node = random.choice(  # Initialize known networks
            yaml.safe_load(
                open('known_nodes.yaml', 'r'))['nodes'])

    def register_node(self, address) -> bool:
        """
        Add a new node with an address
        """
        with self.__block_lock:

            # Get all nodes from seed network
            print(f'http://{self.__seed_node}/nodes')
            request_node = requests.get(f'http://{self.__seed_node}/nodes')
            request_chain = requests.get(f'http://{self.__seed_node}/chain')
            if request_node.status_code == 200 and request_chain.status_code == 200:
                self.__nodes = set(request_node.json()['nodes'])
                self.__chain = request_chain.json()['chain']
            else:
                return False

            # Check if new node already registered
            parsed_url = urlparse(address).netloc
            if parsed_url in self.__nodes:
                return False

            # Broadcast new node to every server
            for node in self.__nodes:
                requests.post(f'http://{node}/nodes/register', json={'node': parsed_url})
            self.__nodes.add(parsed_url)
            return True
