from uuid import uuid4
from flask import Flask, jsonify, request, redirect, render_template
from block_chain import BlockChain

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
our_node_id = str(uuid4()).replace('-', '')

blockchain = BlockChain('seed')


@app.route('/', methods=['GET'])
def index():
    return redirect('/chain')


@app.route('/mine', methods=['GET'])
def mine():
    # Resolve chain
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': "Chain has been synced up, try mining again"
        }
        return jsonify(response), 400

    # Get next proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    new_proof = blockchain.proof_of_work(last_proof)

    # Now that we've found the proof and received our reward...
    # Add the new block to the chain
    previous_hash = blockchain.hash(last_block)
    new_block = blockchain.new_block(new_proof, previous_hash, our_node_id)
    if new_block is not None:
        response = {
            'message': "New block added",
            'index': new_block['index'],
            'transactions': new_block['transactions'],
            'proof': new_block['proof'],
            'previous_hash': new_block['hash_code'],
        }
        return jsonify(response), 200

    response = {
        'message': "Block already mined, try mining again"
    }
    return jsonify(response), 400


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(field in values for field in required):
        return 'Missing required fields', 400

    sender, recipient, amount = values.values()

    _index = blockchain.new_transaction(sender, recipient, amount)

    response = {'message': f'Transaction will be added to block {_index}'}
    return jsonify(response), 200


@app.route('/transactions', methods=['GET'])
def transactions():

    transaction_pool = blockchain.current_transaction
    response = {"transactions_pool": transaction_pool}
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }

    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {'nodes': list(blockchain.nodes),}
    return jsonify(response), 200


@app.route('/nodes/register', methods=['GET'])
def register_nodes():
    node = request.url
    if blockchain.register_node(node):
        response = {
            'message': 'New nodes registered',
            'total_nodes': list(blockchain.nodes)
        }
    else:
        response = {
            'message': 'Node already registered',
        }

    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def broadcast_register_nodes():
    node = request.get_json()['node']
    blockchain.broadcast_register_node(node)

    response = {'message': 'Nodes broadcast',
                'total_nodes': list(blockchain.nodes)}

    return jsonify(response), 200


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    message = None

    if replaced:
        message = 'Chain was replaced'
    else:
        message = 'Current chain is authoritative'

    response = {
        'message': message,
        'chain': blockchain.chain
    }

    return jsonify(response), 200


if __name__ == '__main__':
    app.run()
