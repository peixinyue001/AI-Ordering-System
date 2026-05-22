PINECONE_ENV = "us-east-1"
DASHSCOPE_API_BASE = 'https://dashscope.aliyuncs.com/compatible-mode/v1/'
DASHSCOPE_MODEL_NAME = 'qwen2.5-14b-instruct'


import os
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
AMAP_API_KEY = os.getenv("AMAP_API_KEY")

class AmapConfig:
    AMAP_API_KEY: str = os.getenv("AMAP_API_KEY")
    MERCHANT_LONGITUDE: str = os.getenv("MERCHANT_LONGITUDE", "117.282121")
    MERCHANT_LATITUDE: str = os.getenv("MERCHANT_LATITUDE", "31.851669")
    DELIVERY_RADIUS: int = int(os.getenv("DELIVERY_RADIUS", "2500"))
    DEFAULT_PATH_MODE = os.getenv("DEFAULT_PATH_MODE", "1")

    def __post_init__(self):
        """自动调用"""
        if self.AMAP_API_KEY is None:
            raise ValueError("AMAP_API_KEY不存在")
amap_config = AmapConfig()


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