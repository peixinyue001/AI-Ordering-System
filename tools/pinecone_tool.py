import dashscope
from typing import List, Dict, Any

from pinecone import Pinecone
from pinecone import ServerlessSpec
from http import HTTPStatus
from db_tool import *
from config import *


class   PineconeVectorDB:
    """PineCone向量数据库的操作"""

    def  __init__(self):
        self.pinecone_api_key = PINECONE_API_KEY
        self.dashscope_api_key = DASHSCOPE_API_KEY
        self.pinecone_env = PINECONE_ENV

        # 配置索引名字、嵌入模型名字、嵌入模型的维度
        self.index_name = "menu-item-index"
        self.embedding_model = "text-embedding-v4"
        self.dimension = 1536

        # 配置pinecone客户端对象以及索引对象
        self.pc = None
        self.index = None



    def initialize_connection(self):
        self.pc = Pinecone(api_key=self.pinecone_api_key)

        # 3.初始化索引对象
        if not self.pc.has_index(self.index_name):
            self.pc.create_index(
                name=self.index_name,
                vector_type="dense",
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws",
                                    region=self.pinecone_env)
            )

        #  4. 获取并赋值
        self.index =self.pc.Index(self.index_name)



    def  clear_index_vectors(self):
        """清空指定索引下的向量数据【不是删除索引，索引结构保留，向量数据删除】"""

        if not self.index and not self.initialize_connection():
            return False

        vector_status = self.index.describe_index_stats()
        count = vector_status['total_vector_count']

        if count == 0:
            return True

        self.index.delete(delete_all=True)


    def _embedding_content(self, content :str )->List[float] or None:
        """对文本进行向量化
        args:content:要向量的文本
        :return:文本向量后的结果。[0.1111,0.23,...]
        """
        resp = dashscope.TextEmbedding.call(
            api_key=self.dashscope_api_key,
            model=self.embedding_model,
            input=content,
            dimension=self.dimension
        )

        if resp.status_code == HTTPStatus.OK:
            return resp.output["embeddings"][0]["embedding"]
        return None


    def _splite_content(self ,splite_content :str )->List[str]:
        """切割加载到的菜品信息"""

        from langchain_text_splitters import RecursiveCharacterTextSplitter

        text_spliter = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=0,
            separators=["\n"],
            length_function=len
        )

        docs = text_spliter.create_documents([splite_content])
        clean_docs = []

        for doc in docs:
            clean_content = doc.page_content.strip()
            clean_docs.append(clean_content)

        return clean_docs



    def _validate_datasource(self ,validation_content :str )->bool:
        """校验数据源"""
        if not validation_content:
            return False
        return True





    def upsert_menu_data(self, menu_data: str = None, batch_size: int = 30, clear_existing: bool = True) -> bool:
        """
        将文本向量存储到PineCone向量数据库
        args1:菜品信息
        args2:批量插入向量数据库中的阈值大小
        args3:是否要清空之前索引下的向量数据。
        """

        menu_item_str = menu_data
        if not menu_data:
            menu_item_str = get_all_menu_items()

        if clear_existing:
            self.clear_index_vectors()

        # 2.校验数据源
        if not self._validate_datasource(menu_item_str):
            return False

        # 3.对加载到的数据切分
        embedding_chunks = self._splite_content(menu_item_str)

        # 关键判断：切片为空直接返回
        if not embedding_chunks:
            return False

        # 4.对切分后的chunk进行向量操作
        batch = []
        for line_num, chunk in enumerate(embedding_chunks, 1):
            # a) 对chunk进行向量操作
            vectors_content = self._embedding_content(chunk)

            # b) 判断向量结果
            if not vectors_content or len(vectors_content) != self.dimension:

                return False

            # c) 判断索引对象
            if not self.index and not self.initialize_connection():

                return False

            # d) 准备一些元数据
            menu_medata = {
                "content": chunk,
                "line_number": line_num,
                "dish_id": f"菜品ID:{line_num}",
                "type": "menu_item"
            }
            # e) 准备向量数据的唯一标识
            unique_vector_id = str(line_num)

            batch.append((unique_vector_id, vectors_content, menu_medata))

            # f) 批量插入
            if len(batch) >= batch_size:
                self.index.upsert(vectors=batch)
                batch = []

        if batch:
            self.index.upsert(vectors=batch)

        return True


    def search_similar_menu_item(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """相似性检索"""
        # 1.确保索引存在
        if not self.index and not self.initialize_connection():
            return []

        # 2.生成查询向量
        query_vector = self._embedding_content(query)

        # 3.校验向量有效性
        if not query_vector or len(query_vector) != self.dimension:
            return []

        # 4.执行语义检索
        similar_result = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )

        matches_result = similar_result['matches']
        if not matches_result:
            return []

        final_matches_result = []
        for item in matches_result:
            match_item = {
                "id": item['id'],
                "score": item['score'],
                "content": item['metadata']['content'],
                "line_number": item['metadata']['line_number']
            }
            final_matches_result.append(match_item)

        return final_matches_result


# 定义全局实例
pinecone_db=PineconeVectorDB()



# 定义全局同步向量数据库操作方法
def pinecone_input(menu_data: str = None, clear_existing: bool = True) -> bool:
    """
    将菜品数据输入到Pinecone向量数据库

    Args:
        menu_data: 菜品数据字符串，每行一个菜品的完整信息。如果为None，则从数据库获取
        clear_existing: 是否在插入前清除现有数据，默认为True

    Returns:
        bool: 是否输入成功
    """
    return pinecone_db.upsert_menu_data(menu_data, clear_existing=clear_existing)




# 前端展示用
def search_menu_items_with_ids(query: str, top_k: int = 2) -> Dict[str, Any]:
    """
    根据查询文本搜索相似的菜品
    Args:
        query: str: 查询文本
        top_k: int: 返回的结果数量

    Returns:
        Dict[str,Any]:包含菜品内容列表和真实菜品ID列表的字典
        {
            "contents": [菜品内容列表],
            "ids": [真实菜品ID列表],
            "scores": [相似度分数列表]
        }
    """
    import re

    match_result = pinecone_db.search_similar_menu_item(query=query, top_k=top_k)

    if not match_result:
        return {}

    ids = []
    for item in match_result:
        content = item['content']
        re_match = re.search(r"菜品ID:(\d+)", content)
        dish_id = re_match.group(1) if re_match else item['id']
        ids.append(dish_id)

    return {
        "contents": [item['content'] for item in match_result],
        "ids": ids,
        "scores": [item['score'] for item in match_result]
    }


# if __name__ == "__main__":
