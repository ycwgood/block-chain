import hashlib
import json
import jsonpickle
from time import time
from urllib.parse import urlparse   # url解析
from uuid import uuid4              # 生成唯一id
from flask import Flask, jsonify, request, Response
from typing import Any, Dict, List
import requests
from argparse import ArgumentParser # 命令行参数解析

node_identifier="1"

# 交易
class Transaction:
    def __init__(self, sender, recipient, amount):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount

# 区块
class Block:
    def __init__(self, index, timestamp, transactions, proof, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.proof = proof
        self.previous_hash = previous_hash

# 区块链
class BlockChain:
    def __init__(self):
        self.chain = [] # 存块
        self.current_transactions = [] # 交易实体

        self.nodes = set()  # 无重复的节点集合

        # 创建创世区块
        self.new_block(previous_hash='0')

    # 新建区块
    def new_block(self, previous_hash=None):
        block = Block(len(self.chain) + 1,
                      time(),
                      self.current_transactions,
                      0, 
                      previous_hash or self.hash(self.last_block))
        
        # 非创世区块，做工作量证明
        if previous_hash is None:
            self.proof_of_work(block)

        self.current_transactions = []  # 新建区块打包后重置当前交易信息
        self.chain.append(block)  # 把新建的区块加入链
        return block

    # 添加交易
    def new_transaction(self, sender: str, recipient: str, amount: int) -> int:
        """添加新的交易

        Args:
            sender (str): 发送方
            recipient (str): 接收方
            amount (int): 金额

        Returns:
            int: 返回一个包含此交易的区块序号
        """
        self.current_transactions.append(Transaction(
            sender,
            recipient,
            amount
        ))
        return self.last_block.index + 1


    @staticmethod
    def hash(block: Block) -> str:
        """计算哈希值,返回哈希后的摘要信息

        Args:
            block (Block): 传入一个块

        Returns:
            str: 摘要信息
        """
        block_string = json.dumps(jsonpickle.encode(block, unpicklable=False)).encode()
        return hashlib.sha256(block_string).hexdigest()

    # 获取当前链中最后一个区块
    @property
    def last_block(self) -> Block:  
        return self.chain[-1]
    
    # 工作量证明
    def proof_of_work(self, block: Block) -> int:
        """工作量计算，计算一个符合要求的哈希值

        Args:
            block (Block): 当前区块

        Returns:
            int: 返回符合要求的工作量随机数
        """
        proof = 0
        while self.valid_proof(block, proof) is False:
            proof += 1
        # print(proof)  # 输出计算结果
        return proof

    def valid_proof(self, block: Block, proof: int) -> bool:
        """工作量证明验证，验证计算结果是否以2个0开头

        Args:
            block (Block): 当前区块
            proof (int): 当前工作量证明随机数

        Returns:
            bool: 返回验证是否有效
        """
        block.proof = proof
        hash = self.hash(block)
        # print(guess_hash)  # 输出计算过程
        if hash[0:2] == "00":
            return True
        else:
            return False

    # 验证链是否符合要求
    def vaild_chain(self, chain: List[Block]) -> bool:
        """验证链是否合理：最长且有效

        Args:
            chain (List[Dict[str, Any]]): 传入链

        Returns:
            bool: 返回是否有效
        """
        last_block = chain[0]  # 从第一个创世区块开始遍历验证
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # 如果当前区块的前哈希和前一个计算出来的哈希值不同则是无效链
            if block.previous_hash != self.hash(last_block):
                return False

            # 检验工作量证明是否符合要求
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def register_node(self, address: str) -> None:
        """添加一个新节点到节点集中

        Args:
            address (str): 节点的地址。Eg："http://127.0.0.1:5002"
        """
        parsed_url = urlparse(address)  # 解析url参数
        self.nodes.add(parsed_url.netloc)  # 获取域名服务器


    def resolve_conflicts(self) -> bool:
        """共识算法，解决冲突，以最长且有效的链为主

        Returns:
            bool: 冲突是否解决成功
        """
        neighbours = self.nodes  # 获取节点信息
        new_chain = None  # 定义可能的新链

        max_length = len(self.chain)  # 获取当前链长度

        for node in neighbours:  # 获取节点的链条信息，如果更长且有效则直接替换
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.vaild_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True
        return False


# testPow = BlockChain()
# testPow.proof_of_work(100)

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')  # 使者获取一个唯一的uid
blockChain = BlockChain()

# 查看链接口
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockChain.chain,
        'length': len(blockChain.chain),
    }
    return Response(response=jsonpickle.encode(response, unpicklable=False),
                    status=200,
                    mimetype="application/json")

# 添加交易接口
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return '确少参数', 400

    index = blockChain.new_transaction(values['sender'], values['recipient'],
                                       values['amount'])

    response = {'message': f'交易将会被添加到块 {index}'}
    return jsonify(response), 201

# 打包区块接口
@app.route('/mine', methods=['GET'])
def mine():
    # 发送者为 "0" 表明是新挖出的币,为矿工提供奖励
    blockChain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    block = blockChain.new_block()  # 生成一个新块

    response = {
        'message': "打包成功，新区块已生成！",
        'index': block.index,
        'transactions': block.transactions,
        'proof': block.proof,
        'previous_hash': block.previous_hash,
    }
    return Response(response=jsonpickle.encode(response, unpicklable=False),
                    status=200,
                    mimetype="application/json")

# 节点注册接口
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: 请提供一个符合规则的节点", 400

    for node in nodes:
        blockChain.register_node(node)

    response = {
        'message': '新节点已经被添加！',
        'total_nodes': list(blockChain.nodes),
    }
    return Response(response=jsonpickle.encode(response, unpicklable=False),
                    status=201,
                    mimetype="application/json")

if __name__ == "__main__":

    parser = ArgumentParser()  # 命令行参数解析，端口默认5000
    parser.add_argument('-p',
                        '--port',
                        default=5000,
                        type=int,
                        help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port)  # 启动web服务，默认本机

