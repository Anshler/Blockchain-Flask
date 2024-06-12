import hashlib
import random

import requests
import threading
import json
from time import time
from typing import List, Dict, Set, Any
from urllib.parse import urlparse

import yaml


# The 'original' blockchain, cus we need to start somewhere
class Block:
    def __init__(self, index: int, transactions: List[Dict[str, Any]], proof: int, hash_code: str):
        self.index = index
        self.timestamp = time()
        self.transactions = transactions
        self.proof = proof
        self.hash_code = hash_code

    def get(self) -> Dict[str, Any]:
        return {"index": self.index,
                "timestamp": self.timestamp,
                "transactions": self.transactions,
                "proof": self.proof,
                "hash_code": self.hash_code
                }


class Transaction:
    def __init__(self, sender: str, recipient: str, amount: float):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount

    def get(self) -> Dict[str, Any]:
        return {"sender": self.sender,
                "recipient": self.recipient,
                "amount": self.amount
                }


class BlockChain:
    def __init__(self, mode='normal'):
        self.__chain: List[Dict] = []
        self.__current_transactions: List[Dict] = []
        self.__block_lock = threading.Lock()
        self.__first_block()  # Genesis block
        self.__nodes = set()

        self.__mode = mode
        if self.__mode == 'normal':
            self.__seed_node = random.choice(  # Initialize known networks
                yaml.safe_load(
                    open('known_nodes.yaml', 'r'))['nodes'])

    @property
    def last_block(self) -> Dict:
        return self.__chain[-1]

    @property
    def chain(self) -> List[Dict]:
        return self.__chain

    @property
    def nodes(self) -> Set:
        return self.__nodes

    def __first_block(self) -> Dict:
        block = Block(
            len(self.__chain) + 1,
            self.__current_transactions,
            100,
            "1").get()

        self.__current_transactions = []
        self.__chain.append(block)
        return block

    def new_block(self, proof, previous_hash, our_node_id) -> Dict | None:
        """
        Add a new block to the chain
        """
        with self.__block_lock:
            # Check if the current chain is authoritative (i.e. not replaced/ False)
            if not self.resolve_conflicts():
                # Received reward for finding the proof
                # Sender = 0 to signify this node has MINED a new coin
                self.new_transaction(
                    sender="0",
                    recipient=our_node_id,
                    amount=1
                )
                block = Block(
                    len(self.__chain) + 1,
                    self.__current_transactions,
                    proof,
                    previous_hash).get()

                self.__chain.append(block)
                self.__current_transactions = []
                return block
            return None

    def new_transaction(self, sender, recipient, amount) -> int:
        self.__current_transactions.append(
            Transaction(sender, recipient, amount).get())

        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof) -> int:
        """
        Simple Proof of Work Algorithm:
          - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
          - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        """

        potential_new_proof = 0
        while self.valid_proof(last_proof, potential_new_proof) is False:
            potential_new_proof += 1

        new_proof = potential_new_proof
        return new_proof

    @staticmethod
    def valid_proof(last_proof, new_proof) -> bool:
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param last_proof: <int> Previous Proof
        :param new_proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{last_proof}{new_proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4].startswith("0000")

    def register_node(self, address) -> bool:
        """
        Add a new node with an address
        """
        with self.__block_lock:

            if self.__mode == 'normal':
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

    def broadcast_register_node(self, parsed_url):
        """
        Add a new node with an address (from broadcast POST request)
        :param parsed_url: <str> url of new registered server
        """
        with self.__block_lock:
            self.__nodes.add(parsed_url)

    def valid_chain(self, chain: List[Dict]) -> bool:
        """
        Checks if the chain passed is valid.
        :return: <bool> True if chain is valid, false if not
        """

        previous_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block_under_test = chain[current_index]
            # print(f'Last block: {previous_block}')
            # print(f'Current block on chain under test: {block_under_test}')
            # print("\n--------------\n")

            # Check that the block hash is correct
            if block_under_test['hash_code'] != self.hash(previous_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(previous_block['proof'], block_under_test['proof']):
                return False

            previous_block = block_under_test
            current_index += 1

        return True

    def resolve_conflicts(self) -> bool:
        """
        The consensus algorithm. Resolves conflicts keeping the longest chain in state
        :return: <bool> True if chain was replaced, False if not
        """
        nodes_on_network = self.__nodes
        new_chain = None
        new_nodes = None

        # Keep track of the longest chain we find
        max_length = len(self.__chain)
        # Fetch all chains from all nodes
        for node in nodes_on_network:
            response = requests.get(f'http://{node}/chain')
            response_node = requests.get(f'http://{node}/nodes')
            if response.status_code == 200 and response_node.status_code == 200:
                response_json = response.json()
                neighbor_node_length = response_json['length']
                neighbor_node_chain = response_json['chain']

                if neighbor_node_length > max_length and self.valid_chain(neighbor_node_chain):
                    max_length = neighbor_node_length
                    new_chain = neighbor_node_chain
                    new_nodes = response_node.json()['nodes']

        if new_chain:
            self.__chain = new_chain
            self.__nodes = new_nodes
            return True

        return False

    @staticmethod
    def hash(block: Dict) -> str:
        """
        Calculates the SHA-256 hash of the block data.
        """
        hash_string = hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()
        return hash_string
