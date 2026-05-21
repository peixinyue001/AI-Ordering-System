import os
import requests
from urllib3 import Retry
from requests.adapters import HTTPAdapter
from dataclasses import dataclass
from typing import Dict, Any, Optional, Literal, Union

from dotenv import load_dotenv

from config import *

load_dotenv()


PathInputModel = Literal["1", "2", "3"]  # 外部用
PathModel = Literal["walking", "electrobike", "driving"]  # 内部


# 路径模式转换工具
class PathModeConverter:
    """路径模式转换工具类"""

    # 映射关系  外部输入的路径模式 -> 内部使用的路径模式
    MODE_MAPPING = {
        "1": "walking",
        "2": "electrobike",
        "3": "driving",

    }

    @classmethod
    def to_mode(cls, mode_input: Union[PathInputModel]) -> PathModel:
        """将输入的模式转换为内部使用的模式"""

        if mode_input in cls.MODE_MAPPING:
            return cls.MODE_MAPPING[mode_input]
        else:
            raise ValueError(f"不支持的路径模式: {mode_input}，支持的模式: {list(cls.MODE_MAPPING.keys())}")





def create_session_with_retries():
    session = requests.Session()
    retry_strategy = Retry(
        total = 3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504, 505]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def safe_request(base_url: str, params: dict) -> Optional[Dict]:
    # 创建带重试的请求会话
    session = create_session_with_retries()

    # 1. 先尝试 HTTPS 请求
    try:
        response = session.get(base_url, params=params, timeout=10)
        return response.json()
    except:
        pass

    # 2. HTTPS 失败了，自动换成 HTTP 再试一次
    try:
        http_url = base_url.replace("https://", "http://")
        response = session.get(http_url, params=params, timeout=10)
        return response.json()
    except:
        pass

    # 都失败返回 None
    return None

def geocode_address(address: str) -> Dict[str, Any]:
    """地址转经纬度（地理编码）"""
    # 1. 高德地图地理编码API地址
    request_url = "https://restapi.amap.com/v3/geocode/geo"

    # 2. 拼接请求参数：地址 + API密钥
    params = {
        "address": address,
        "key": amap_config.AMAP_API_KEY
    }

    # 3. 发送HTTPS请求，失败自动切HTTP
    response = safe_request(request_url, params)

    # 4. 高德返回失败
    if response['status'] != "1":
        return {
            "success": False,
            "message": response['info']
        }

    # 5. 高德返回成功 → 取出经纬度和地址
    geocodes = response['geocodes'][0]
    return {
        "formatted_address": geocodes['formatted_address'],
        "location": geocodes['location'],
        "success": True,
    }

def calculate_distance(origin_location: str, destination_location: str, path_mode_input: PathInputModel | None) -> Dict[str, Any]:
    """计算两个经纬度之间的距离和时间"""

    # 1. 把外部输入的 1/2/3 转换成内部用的 walking/electrobike/driving
    inner_mode = PathModeConverter.to_mode(path_mode_input)

    # 2. 三种模式对应三个不同的高德API地址
    path_endpoint = {
        "walking": "https://restapi.amap.com/v5/direction/walking",
        "electrobike": "https://restapi.amap.com/v5/direction/electrobike",
        "driving": "https://restapi.amap.com/v5/direction/driving"
    }

    # 3. 构造请求参数
    params = {
        "key": amap_config.AMAP_API_KEY,
        "origin": origin_location,
        "destination": destination_location
    }

    # 4. 驾车模式需要额外加参数才能返回时间
    if inner_mode == "driving":
        params["show_fields"] = "cost"

    # 5. 发送请求（HTTPS失败自动切HTTP）
    response = safe_request(path_endpoint[inner_mode], params)

    # 6. 从返回结果里拿路径数据
    path = response['route']['paths'][0]

    # 7. 电动车时间在外面，步行/驾车时间在cost里
    if inner_mode == "electrobike":
        duration = path['duration']
    else:
        duration = path['cost']['duration']

    # 8. 返回结果：距离、时间、成功状态
    return {
        "distance": int(path["distance"]),
        "duration": duration,
        "success": True
    }



if __name__ == "__main__":
    result = calculate_distance(
        origin_location="117.282121,31.851669",  # 起点经纬度
        destination_location="117.294126,31.844542",  # 终点经纬度
        path_mode_input="3"  # 3=驾车
    )
    print(result)
