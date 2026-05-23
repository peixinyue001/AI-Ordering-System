"""
智能点餐助手主程序
LangChain中Agent组件的作用:根据自然语言选择工具，调用工具。
该程序构建了一个包含工具选择功能的LLM系统(相当于LangChain中的Agent角色)，能够：
1. 自动选择合适的工具（常规咨询、菜品推荐、配送范围检查）
2. 调用相应工具并返回结果
3. 提供自然、友好的对话体验
手动实现Agent的机制（找工具 调用工具）

"""
from json import JSONDecodeError
from typing import Dict, List, Any
from tools.llm_tool import call_llm
from agent.mcp import general_inquiry, menu_inquiry, delivery_check_tool
import json
import time


class SmartRestaurantAssistant:
    """小助手类【Agent】"""
    def __init__(self):
        # 给Agent封装工具进去  tools未来需要封装工具的名字（函数的名字）和工具的对象（函数对象）
        self.tools = {
            "general_inquiry": general_inquiry,
            "menu_inquiry": menu_inquiry,
            "delivery_check_tool": delivery_check_tool
        }

        self.instruction = """你是一个智能餐厅助手的意图分析器。
        请分析用户问题意图，并且选择最合适的工具来处理：

        工具说明：
        1. general_inquiry: 处理餐厅常规咨询（营业时间、地址、电话、优惠活动、预约等）
        2. menu_inquiry: 处理智能菜品推荐和咨询（推荐菜品、介绍菜品、询问菜品信息、点餐等）
        3. delivery_check_tool: 处理配送范围检查（查询某个地址是否在配送范围内、能否送达等）

        你必须严格按照以下JSON格式返回，不要包含任何其他文字：
        {
            "tool_name": "工具名称",
             "format_query": "处理后的用户问题"
        }

        正确示例：
        用户："你们几点营业？" -> {"tool_name": "general_inquiry", "format_query": "营业时间"}
        用户："推荐川菜系列的菜品" -> {"tool_name": "menu_inquiry", "format_query": "推荐川菜"}
        用户："能送到武汉大学吗？" -> {"tool_name": "delivery_check_tool", "format_query": "武汉大学"}

        重要规则：
        - 只返回纯JSON，不要有任何额外字符和解释
        - 确保JSON格式完全正确
        - tool_name必须是以下之一：general_inquiry, menu_inquiry, delivery_check_tool
        - format_query要简洁明了地概括用户问题

        记住：如果你错误的选择工具，你会受到惩罚，系统将面临崩溃。"""

        self.max_retries = 3
        self.backoff = 1

    def _clean_llm_response(self, llm_response_content: str) -> str:
        """清洗LLM的字符串内容"""
        if llm_response_content.startswith("```json"):
            llm_response_content = llm_response_content[7:]
        if llm_response_content.endswith("```"):
            llm_response_content = llm_response_content[:-3]

        star_index = llm_response_content.find("{")
        end_index = llm_response_content.rfind("}")

        if star_index != -1 and end_index != -1 and end_index > star_index:
            clean_response = llm_response_content[star_index:end_index + 1]
            return clean_response

    def _analyse_intention_fallback(self, user_query: str) -> Dict[str, Any]:
        delivery_keywords = ["配送", "送达", "送到", "送货", "外卖", "地址", "区域", "范围"]
        menu_keywords = ["菜单", "菜品", "推荐", "点餐", "招牌", "特色", "什么好吃", "有什么菜"]

        if any(keyword in user_query for keyword in delivery_keywords):
            return {"tool_name": "delivery_check_tool", "format_query": user_query}
        elif any(keyword in user_query for keyword in menu_keywords):
            return {"tool_name": "menu_inquiry", "format_query": user_query}
        else:
            return {"tool_name": "general_inquiry", "format_query": user_query}

    def _analyse_intention(self, user_query: str, last_error: str) -> Dict[str, Any]:
        instruction = self.instruction
        if last_error:
            instruction += f"\n\n上次解析失败，错误信息：{last_error}\n请根据错误信息修正JSON格式，确保返回正确的JSON。"

        llm_response = call_llm(user_query, instruction)
        clean_response = self._clean_llm_response(llm_response)
        llm_response_dict = json.loads(clean_response)

        return llm_response_dict

    def analyse_intention_with_retry(self, user_query: str) -> Dict[str, Any]:
        last_error = None
        for i in range(self.max_retries):
            try:
                llm_response_dict = self._analyse_intention(user_query, last_error)
                return llm_response_dict
            except (ValueError, JSONDecodeError) as e:
                last_error = str(e)

                if i < self.max_retries - 1:
                    time.sleep(self.backoff)

        return self._analyse_intention_fallback(user_query)

    def execute_tool(self, tool_name: str, tool_param: str) -> Dict[str, Any] | str:
        tool_obj = self.tools[tool_name]

        if tool_name == "general_inquiry":
            tool_result = tool_obj.invoke({"query": tool_param})
        elif tool_name == "menu_inquiry":
            tool_result = tool_obj.invoke({"query": tool_param})
        else:
            tool_result = tool_obj.invoke({"address": tool_param, "travel_mode": "2"})
        return tool_result

    def invoke(self, user_query: str):
        """和小助手（Agent）聊天"""
        structured_tool = self.analyse_intention_with_retry(user_query)
        tool_name = structured_tool['tool_name']
        tool_param = structured_tool['format_query']
        print(f"工具信息->名字:{tool_name}:参数:{tool_param}")

        tool_result = self.execute_tool(tool_name, tool_param)
        return tool_result


# 全局方法（给service调用）【成员：方法 变量】
def chat_with_assistant(user_query: str):
    """和智能小助手对话"""
    assistant = SmartRestaurantAssistant()
    assistant_response = assistant.invoke(user_query or "介绍您们餐厅的基本信息")
    print(f"小助手的回复:\n{assistant_response}")
    return assistant_response


if __name__ == '__main__':
    pass