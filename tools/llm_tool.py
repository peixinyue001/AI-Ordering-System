import os

from langchain_openai import  ChatOpenAI
from langchain_core.prompts import  ChatPromptTemplate
from config import *

from dotenv import load_dotenv
load_dotenv()


def call_llm(query: str, system_instruction: str) -> str:
    """通用大模型调用函数"""

    # 1. 从环境变量读取配置
    api_key = os.getenv("DASHSCOPE_API_KEY")
    api_base = DASHSCOPE_API_BASE
    model_name = DASHSCOPE_MODEL_NAME

    # 2. 创建大模型对象
    llm = ChatOpenAI(
        model_name=model_name,
        openai_api_key=api_key,
        openai_api_base=api_base
    )

    # 3. 创建提示词模板
    chat_prompt_template = ChatPromptTemplate.from_messages([
        ("system", "{system_instruction}"),
        ("human", "{query}"),
    ])

    # 4. 用 LCEL 语法组装链
    chain = chat_prompt_template | llm

    # 5. 执行链，获取结果
    response = chain.invoke({
        "system_instruction": system_instruction,
        "query": query
    })

    # 6. 返回模型回答文本
    return response.content

if __name__=="__main__":
    result = call_llm(query="当下AI就业环境到底怎么样？", system_instruction="您是一位AI就业分析的市场专家，请客观回答用户询问的就业问题")
    print(result)