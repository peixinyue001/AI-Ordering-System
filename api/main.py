from pydantic import BaseModel
from typing import List
from fastapi import FastAPI

app = FastAPI(title='智能点餐助手的API接口')

# 定义菜品列表响应模型


class MenuListResponse(BaseModel):
    """菜品列表响应"""
    success: bool
    menu_items: List[dict]  # 菜品列表
    count: int  # 菜品数
    message: str  # 响应消息提示

@app.get('/')
def hello_world():
    return {'hello': 'world'}



@app.get('/healty')
def healty():
    return{'message': 'the route to be requested'}


@app.get("/menu/list", response_model=MenuListResponse)
async def menu_list_endpoint():
    """菜品列表区域展示"""
    # 1.调用service
    from service.diancan_service import get_menu
    # 2.调用方法
    menu_items=get_menu()
    # 3.封装结果返回
    if  not  menu_items:
        return MenuListResponse(
            success=False,
            menu_items=[],
            count=0,
            message="暂无菜品列表可用"
        )

    return MenuListResponse(
        success=True,
        menu_items=menu_items,
        count=len(menu_items),
        message=f"成功查询到{len(menu_items)}道菜品信息"
    )




