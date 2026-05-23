"""
LangChain 三个工具实现
工具1：常规问答
工具2：菜品查询
工具3：配送范围检查
"""
import os
from langchain_core.tools import tool
from tools.llm_tool import call_llm
from tools.pinecone_tool import search_menu_items_with_ids
from tools.amap_tool import check_delivery_range, PathInputModel
from typing import Dict, Any


# 加载提示词文件
def load_prompt_template(prompt_file_name):
    current_file_path = os.path.abspath(__file__)
    current_file_dir = os.path.dirname(current_file_path)
    project_dir = os.path.dirname(current_file_dir)
    prompt_path = os.path.join(project_dir, "prompt", f"{prompt_file_name}.txt")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


# 工具1：常规问题
@tool
def general_inquiry(query: str) -> str:
    """处理餐厅介绍、营业时间、联系方式、优惠等常规问题"""
    prompt_template = load_prompt_template("general_inquiry")
    full_query = f"用户问题：{query}"
    llm_response = call_llm(full_query, prompt_template)
    return llm_response


# 工具2：菜品查询
@tool
def menu_inquiry(query: str) -> Dict[str, Any]:
    """处理菜品介绍、推荐、价格、口味等问题"""
    prompt_template = load_prompt_template("menu_inquiry")
    similar_result = search_menu_items_with_ids(query)

    if similar_result and similar_result['contents']:
        menu_context = "\n".join([f"-{item}" for item in similar_result['contents']])
        full_query = f"菜品信息：{menu_context}\n用户问题：{query}"
    else:
        full_query = f"用户问题：{query}"

    llm_response = call_llm(full_query, prompt_template)

    menu_ids = similar_result.get('ids', [])

    return {
        "recommendation": llm_response,
        "menu_ids": similar_result['ids']
    }


# 工具3：配送范围检查
@tool
def delivery_check_tool(address: str, travel_mode: PathInputModel) -> str:
    """检查地址是否在配送范围"""
    result = check_delivery_range(address, travel_mode)

    if result["status"] == "success":
        status_text = "✅ 可以配送" if result["in_range"] else "❌ 超出范围"
        response = f"""
配送地址：{result['formatted_address']}
配送距离：{result['distance']}公里
配送状态：{status_text}
        """.strip()
    else:
        response = "查询失败"

    return response


# 导出所有工具
ALL_TOOLS = [general_inquiry, menu_inquiry, delivery_check_tool]


if __name__ == '__main__':
    # general_inquiry_result = general_inquiry.invoke({'query':"请问您们餐厅的营业时间是什么时候?"})
    # print(general_inquiry_result)

    menu_inquiry_result = menu_inquiry.invoke({"query": "请给我推荐四喜丸子"})
    print(menu_inquiry_result)

