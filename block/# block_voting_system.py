# block_voting_system.py
from flask import Flask, jsonify, request
import hashlib
import json
from time import time
from uuid import uuid4

# ---------------- Blockchain Class ---------------- #
class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_votes = []

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block and add it to the chain
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'votes': self.current_votes,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of votes
        self.current_votes = []
        self.chain.append(block)
        return block

    def new_vote(self, voter_id, candidate):
        """
        Creates a new vote to go into the next mined Block
        """
        self.current_votes.append({
            'voter_id': voter_id,
            'candidate': candidate,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """
        Returns the last Block in the chain
        """
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p such that hash(pp') contains 4 leading zeroes
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


# ---------------- Flask App ---------------- #
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route('/vote', methods=['POST'])
def vote():
    values = request.get_json()

    required = ['voter_id', 'candidate']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Add a new vote
    index = blockchain.new_vote(values['voter_id'], values['candidate'])
    response = {'message': f'Your vote will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Reward for finding the proof
    blockchain.new_vote(voter_id="0", candidate=node_identifier)

    # Forge the new Block
    block = blockchain.new_block(proof)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'votes': block['votes'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/results', methods=['GET'])
def results():
    """
    Count votes for each candidate
    """
    vote_count = {}
    for block in blockchain.chain:
        for vote in block['votes']:
            candidate = vote['candidate']
            if candidate != "0":  # Ignore system reward
                vote_count[candidate] = vote_count.get(candidate, 0) + 1
    return jsonify(vote_count), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
