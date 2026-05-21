PINECONE_ENV = "us-east-1"
DASHSCOPE_API_BASE = 'https://dashscope.aliyuncs.com/compatible-mode/v1/'
DASHSCOPE_MODEL_NAME = 'qwen2.5-14b-instruct'

import os
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")


# 数据库连接
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'menu'
}

if __name__ == "__main__":
    print(PINECONE_API_KEY)