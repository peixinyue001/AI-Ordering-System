import pymysql
from pymysql.cursors import DictCursor
from typing import List, Dict, Any
from config import *


# 读取MySQL工具类
class MysqlReader:
    def __init__(self):
        self.connection = pymysql.connect(**MYSQL_CONFIG)
        self.cursor = self.connection.cursor(DictCursor)
    # 查询MySQL，读取数据
    def read(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    # 关闭
    def close(self):
        self.cursor.close()
        self.connection.close()


def get_all_menu_items():
    reader = MysqlReader()
    sql = """
                SELECT id, dish_name, price, description, category, 
                spice_level, flavor, main_ingredients, cooking_method, 
                is_vegetarian, allergens, is_available
                FROM menu_items
                WHERE is_available = 1
                ORDER BY category, dish_name
                """
    menu_items = reader.read(sql)
    reader.close()

    if not menu_items:
        return "当前无可用的菜品信息"

    menu_items_strings = []
    for item in menu_items:
        # 1.格式化辣度级别
        spice_level_mapping = {0: "不辣", 1: "微辣", 2: "中辣", 3: "重辣"}
        format_spice_level = spice_level_mapping.get(item.get('spice_level'), "暂无辣度级别")
        # 2.格式化是否是素食
        format_is_vegetarian = "是" if item.get('is_vegetarian') else "否"
        # 3.格式化菜品描述
        format_description = item.get('description') if item.get('description', '').strip() else "暂无描述"
        # 4.格式化主要食材
        format_main_ingredients = item.get('main_ingredients') if item.get('main_ingredients',
                                                                           '').strip() else "暂无主要食材"
        # 5.格式化过敏源
        format_allergens = item.get('allergens') if item.get('allergens', '').strip() else "暂无过敏源"

        # 拼接菜品结构为字符串
        menu_item_string = f"菜品ID:{item['id']}|菜品名称:{item['dish_name']}|价格:¥{item['price']:.2f}|菜品描述:{format_description}|分类:{item['category']}|辣度:{format_spice_level}|口味:{item['flavor']}|主要食材:{format_main_ingredients}|烹饪方法:{item['cooking_method']}|素食:{format_is_vegetarian}|过敏原:{format_allergens}"
        menu_items_strings.append(menu_item_string)

    return  "\n".join(menu_items_strings)


def get_menu_items() -> List[Dict[str, Any]]:
    reader = MysqlReader()
    sql = """
                SELECT id, dish_name, price, description, category, 
                spice_level, flavor, main_ingredients, cooking_method, 
                is_vegetarian, allergens, is_available
                FROM menu_items
                WHERE is_available = 1
                ORDER BY category, dish_name
                """
    menu_items = reader.read(sql)
    reader.close()

    if not menu_items:
        return []

    menu_items_list = []

    for item in menu_items:
        # 辣度等级转换
        spice_levels = {0: "不辣", 1: "微辣", 2: "中辣", 3: "重辣"}
        spice_text = spice_levels.get(item['spice_level'], "未知")

        # 处理数据
        processed_item = {
            "id": item['id'],
            "dish_name": item['dish_name'],
            "price": float(item['price']),
            "formatted_price": f"¥{item['price']:.2f}",
            "description": item['description'] or "暂无描述",
            "category": item['category'],
            "spice_level": item['spice_level'],
            "spice_text": spice_text,
            "flavor": item['flavor'] or "暂无口味",
            "main_ingredients": item['main_ingredients'] or "暂无主要食材",
            "cooking_method": item['cooking_method'] or "暂无烹饪方法",
            "is_vegetarian": bool(item['is_vegetarian']),
            "vegetarian_text": "是" if item['is_vegetarian'] else "否",
            "allergens": item['allergens'] if item['allergens'] and item['allergens'].strip() else "暂无过敏原",
            "is_available": bool(item['is_available'])
        }
        menu_items_list.append(processed_item)

    return menu_items_list


