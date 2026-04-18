#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天天基金网 API 封装模块

提供基金数据获取的统一接口。
"""

import re
import json
from typing import Optional, List, Dict

from .http_client import fetch_text, fetch_json, get_session


API_BASE = "https://fund.eastmoney.com"


def get_fund_info(fund_code: str) -> Dict:
    """
    获取基金基本信息（从 pingzhongdata JS 文件）

    Args:
        fund_code: 基金代码

    Returns:
        包含基金名称、代码、收益率等信息的字典
    """
    url = f"{API_BASE}/pingzhongdata/{fund_code}.js"
    content = fetch_text(url)

    if not content:
        return {}

    fund_info = {'code': fund_code}

    # 提取基金名称
    match = re.search(r'fS_name\s*=\s*"([^"]+)"', content)
    if match:
        fund_info['name'] = match.group(1)

    # 提取收益率
    syl_fields = {
        'syl_1n': 'return_1y',
        'syl_6y': 'return_6m',
        'syl_3y': 'return_3m',
        'syl_1y': 'return_1m',
    }

    for js_field, info_field in syl_fields.items():
        match = re.search(rf'{js_field}\s*=\s*"([^"]+)"', content)
        if match:
            fund_info[info_field] = f"{match.group(1)}%"

    return fund_info


def get_stock_codes(fund_code: str) -> List[Dict]:
    """
    获取基金重仓股票代码列表

    Args:
        fund_code: 基金代码

    Returns:
        股票代码列表，每个元素为 {'code': '600519', 'market': 'SH'}
    """
    url = f"{API_BASE}/pingzhongdata/{fund_code}.js"
    content = fetch_text(url)

    if not content:
        return []

    # 解析 stockCodesNew
    match = re.search(r'var\s+stockCodesNew\s*=\s*(\[.*?\]);', content)
    if not match:
        return []

    stock_codes = json.loads(match.group(1))
    stocks = []

    for code in stock_codes:
        parts = code.split('.')
        if len(parts) == 2:
            # 过滤债券代码
            sec_code = parts[1]
            if not re.match(r'1[12][378]\d{3}', sec_code):
                market = 'SH' if parts[0] == '1' else 'SZ'
                stocks.append({'code': parts[1], 'market': market, 'full_code': code})

    return stocks


def get_fund_list() -> List[List]:
    """
    获取所有基金列表

    Returns:
        基金列表，每个元素为 [代码，名称，类型，...]
    """
    url = f"{API_BASE}/js/fundcode_search.js"
    content = fetch_text(url, encoding='utf-8-sig')  # 处理 UTF-8 BOM

    if not content:
        return []

    try:
        content = content.strip()
        if content.startswith('var r = '):
            content = content[8:]
        if content.endswith(';'):
            content = content[:-1]
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"解析基金列表失败：{e}")
        return []


def get_holder_structure(fund_code: str) -> Optional[Dict]:
    """
    获取基金持有人结构（机构/个人占比）

    Args:
        fund_code: 基金代码

    Returns:
        包含机构和个人持有比例的字典
    """
    url = f"{API_BASE}/pingzhongdata/{fund_code}.js"
    content = fetch_text(url)

    if not content:
        return None

    match = re.search(r'Data_holderStructure\s*=\s*({.+?});', content, re.DOTALL)
    if not match:
        return None

    try:
        holder_data = json.loads(match.group(1))
        series = holder_data.get("series", [])
        categories = holder_data.get("categories", [])

        if not series or not categories:
            return None

        latest_idx = len(categories) - 1
        inst_ratio = 0.0
        personal_ratio = 0.0

        for item in series:
            name = item.get("name", "")
            data = item.get("data", [])
            if data and len(data) > latest_idx:
                value = data[latest_idx]
                if "机构" in name:
                    inst_ratio = value
                elif "个人" in name:
                    personal_ratio = value

        return {
            "机构持有比例": inst_ratio,
            "个人持有比例": personal_ratio,
            "日期": categories[latest_idx],
        }
    except (json.JSONDecodeError, KeyError):
        return None


def get_historical_nav(fund_code: str, page_size: int = 365) -> Optional[List[Dict]]:
    """
    获取基金历史净值数据

    Args:
        fund_code: 基金代码
        page_size: 获取天数

    Returns:
        净值数据列表
    """
    url = "http://api.fund.eastmoney.com/f10/lsjz"
    params = {
        "fundCode": fund_code,
        "pageIndex": 1,
        "pageSize": page_size,
    }

    data = fetch_json(url, params=params)
    if not data:
        return None

    if data.get("ErrCode") == 0 and data.get("Data"):
        return data["Data"]["LSJZList"]

    return None


def get_nav_trend(fund_code: str) -> List[Dict]:
    """
    获取基金净值走势数据（单位净值和累计净值）

    Args:
        fund_code: 基金代码

    Returns:
        包含净值和累计净值的列表
    """
    url = f"{API_BASE}/pingzhongdata/{fund_code}.js"
    content = fetch_text(url)

    if not content:
        return []

    result = []

    # 提取单位净值数据
    net_worth_match = re.search(r'Data_netWorthTrend\s*=\s*(\[.*?\]);', content, re.DOTALL)
    # 提取累计净值数据
    ac_worth_match = re.search(r'Data_ACWorthTrend\s*=\s*(\[.*?\]);', content, re.DOTALL)

    if net_worth_match:
        net_worth_data = json.loads(net_worth_match.group(1))

        # 解析累计净值数据
        ac_worth_dict = {}
        if ac_worth_match:
            try:
                ac_worth_raw = json.loads(ac_worth_match.group(1))
                if ac_worth_raw and isinstance(ac_worth_raw[0], list):
                    for item in ac_worth_raw:
                        if len(item) >= 2:
                            ac_worth_dict[str(item[0])] = item[1]
            except Exception:
                pass

        # 合并数据
        for item in net_worth_data:
            x_val = str(item.get('x', ''))
            y_val = item.get('y', 0)
            ac_value = ac_worth_dict.get(x_val, y_val)

            result.append({
                'x': x_val,
                'DWJZ': y_val,
                'LJJZ': ac_value,
            })

    return result


def get_fund_scale(fund_code: str) -> str:
    """
    获取基金规模（亿元）

    Args:
        fund_code: 基金代码

    Returns:
        基金规模字符串
    """
    url = f"{API_BASE}/pingzhongdata/{fund_code}.js"
    content = fetch_text(url)

    if not content:
        return "N/A"

    # 获取 Data_fluctuationScale 数据
    match = re.search(r'Data_fluctuationScale\s*=\s*({[^;]+});', content)
    if match:
        try:
            data = json.loads(match.group(1))
            categories = data.get("categories", [])
            series = data.get("series", [])

            if categories and series:
                values = [(cat, item.get("y", 0)) for cat, item in zip(categories, series)]
                valid_values = [(cat, v) for cat, v in values if v and v > 0]
                if valid_values:
                    latest_cat, latest_scale = valid_values[-1]
                    return str(round(latest_scale, 2))
        except Exception:
            pass

    return "N/A"
