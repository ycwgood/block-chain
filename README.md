# block-chain

## python虚拟环境
- 安装依赖
  pip install pipenv
- 创建环境
  pipenv install
  会生成一个pipfile文件，用于管理库的依赖
- 在虚拟环境中安装依赖
  pipenv install flask==2.0.2
  pipenv install requests==2.18.4
  pipenv install jsonpickle
- 启动虚拟环境
  pipenv shell

## 代码思路
### 三个类型
#### Transaction 交易
一条交易有sender, recipient, amount组成
#### Block 区块
一个区块有区块号，时间戳，交易列表，工作量证明，上一个区块Hash号组成
#### BlockChain 区块链
一个区块链有一系列区块列表组成
还有参与这个区块链的工作节点集合

### 区块链支持的操作
#### 新建（打包）区块
BlockChain.new_block()
其中的区块工作量字段(Block.proof)需要消耗计算资源才能生成
#### 添加交易
BlockChain.new_transaction()
#### 验证区块链
BlockChain.vaild_chain()

### Web接口
#### /chain
查看整条区块链
#### /transactions/new
添加交易
#### /mine
打包区块


