#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金业绩分析模块

获取基金近 1 年收益走势数据。
"""

import csv
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from core.config import get_output_dir
from core.http_client import fetch_text, fetch_json


def get_nav_trend_with_growth(fund_code: str) -> List[Dict]:
    """
    获取基金净值走势数据（含增长率）

    Args:
        fund_code: 基金代码

    Returns:
        包含日期、净值、增长率的列表
    """
    # 从 JS 文件获取净值和累计净值数据
    url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
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


def get_historical_nav_detail(fund_code: str, page_size: int = 365) -> List[Dict]:
    """
    获取基金历史交易数据（包含日增长率）

    Args:
        fund_code: 基金代码
        page_size: 获取天数

    Returns:
        历史净值数据列表
    """
    url = "http://api.fund.eastmoney.com/f10/lsjz"
    params = {
        "fundCode": fund_code,
        "pageIndex": 1,
        "pageSize": page_size,
    }

    data = fetch_json(url, params=params)
    if not data:
        return []

    if data.get("ErrCode") == 0 and data.get("Data"):
        return data["Data"]["LSJZList"]

    return []


def timestamp_to_date(timestamp_ms: str) -> str:
    """将毫秒时间戳转换为日期字符串"""
    try:
        timestamp = int(float(timestamp_ms))
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return str(timestamp_ms)


def filter_last_year(data: list) -> list:
    """筛选近 1 年的数据"""
    if not data:
        return []

    now = datetime.now()
    one_year_ago = now.replace(year=now.year - 1)

    result = []
    for item in data:
        try:
            x_val = item.get("x", "")
            date_str = timestamp_to_date(x_val)
            item_date = datetime.strptime(date_str, "%Y-%m-%d")

            if item_date >= one_year_ago:
                item["_date_str"] = date_str
                result.append(item)
        except Exception:
            continue

    return result


def merge_and_process_data(js_data: list, detail_data: list) -> list:
    """合并和处理数据，计算增长率"""
    # 创建详细数据映射
    detail_map = {}
    for item in detail_data:
        date = item.get("FSRQ", "")
        detail_map[date] = {
            "DWJZ": float(item.get("DWJZ", 0)),
            "LJJZ": float(item.get("LJJZ", 0)),
            "JZZZL": float(str(item.get("JZZZL", "0")).replace("%", "")),
        }

    result = []
    for item in js_data:
        date_str = item.get("_date_str", "")
        net_value = float(item.get("DWJZ", 0))
        detail = detail_map.get(date_str, {})

        if detail:
            accumulated_value = detail.get("LJJZ", net_value)
            daily_growth = detail.get("JZZZL", 0.0)
        else:
            accumulated_value = float(item.get("LJJZ", net_value))
            daily_growth = 0.0

        result.append({
            "日期": date_str,
            "单位净值": net_value,
            "累计净值": accumulated_value,
            "日增长率 (%)": daily_growth,
        })

    result.sort(key=lambda x: x["日期"])

    # 如果日增长率都是 0，手动计算
    if all(item["日增长率 (%)"] == 0.0 for item in result):
        for i in range(1, len(result)):
            prev_value = result[i - 1]["单位净值"]
            curr_value = result[i]["单位净值"]
            if prev_value > 0:
                growth = (curr_value - prev_value) / prev_value * 100
                result[i]["日增长率 (%)"] = round(growth, 2)

    # 计算累计收益率
    if result:
        base_value = result[0]["单位净值"]
        for item in result:
            if base_value > 0:
                item["累计收益率 (%)"] = round(
                    (item["单位净值"] - base_value) / base_value * 100, 2
                )
            else:
                item["累计收益率 (%)"] = 0.0

    return result


def fetch_fund_performance(fund_code: str) -> List[Dict]:
    """
    获取基金业绩数据（完整流程）

    Args:
        fund_code: 基金代码

    Returns:
        业绩数据列表
    """
    # 1. 从 JS 文件获取净值数据
    js_data = get_nav_trend_with_growth(fund_code)
    if not js_data:
        return []

    # 2. 从 API 获取历史交易数据
    detail_data = get_historical_nav_detail(fund_code)

    # 3. 筛选近 1 年数据
    filtered_data = filter_last_year(js_data)

    # 4. 合并和处理数据
    return merge_and_process_data(filtered_data, detail_data)


def save_performance_to_csv(data: List[Dict], fund_code: str, filename: str = None) -> Optional[Path]:
    """
    保存业绩数据到 CSV

    Args:
        data: 数据列表
        fund_code: 基金代码
        filename: 文件名

    Returns:
        保存的文件路径
    """
    if not data:
        print("没有数据可保存")
        return None

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fund_{fund_code}_{timestamp}.csv"

    output_dir = get_output_dir()
    output_path = output_dir / filename

    fieldnames = ["日期", "单位净值", "累计净值", "日增长率 (%)", "累计收益率 (%)"]

    try:
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(f"数据已保存到：{output_path}")
        return output_path
    except Exception as e:
        print(f"保存文件失败：{e}")
        return None
