#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机构持有基金分析模块

查找机构持有占比高于指定阈值的基金。
"""

import csv
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from core.config import get_output_dir
from core.http_client import fetch_text
from core.tiantian_api import get_fund_list, get_holder_structure, get_fund_scale


def search_institution_funds(threshold: float = 30.0, target_count: int = 100) -> List[Dict]:
    """
    搜索机构持有占比高于指定阈值的基金

    Args:
        threshold: 机构持有占比阈值（%）
        target_count: 目标找到数量

    Returns:
        符合条件的基金列表
    """
    result = []

    print(f"开始查找机构持有占比 > {threshold}% 的基金...")
    print(f"找到 {target_count} 只符合条件的基金后停止")
    print("-" * 60)

    fund_list = get_fund_list()
    if not fund_list:
        print("获取基金列表失败")
        return result

    processed = 0
    for fund in fund_list:
        if len(result) >= target_count:
            break

        try:
            fund_code = fund[0]
            fund_name = fund[1]
            fund_type = fund[2] if len(fund) > 2 else ""

            # 跳过货币基金
            if "货币" in fund_type:
                continue

            # 获取持有人结构
            holder = get_holder_structure(fund_code)

            if holder and holder.get("机构持有比例"):
                inst_ratio = holder["机构持有比例"]
                personal_ratio = holder.get("个人持有比例", 0)

                processed += 1

                if inst_ratio > threshold:
                    # 获取基金规模
                    fund_scale = get_fund_scale(fund_code)

                    fund_result = {
                        "基金代码": fund_code,
                        "基金名称": fund_name,
                        "基金类型": fund_type,
                        "机构持有占比 (%)": round(inst_ratio, 2),
                        "个人持有占比 (%)": round(personal_ratio, 2),
                        "基金规模 (亿元)": fund_scale,
                    }
                    result.append(fund_result)
                    print(f"✓ [{fund_code}] {fund_name}: 机构持有 {inst_ratio:.2f}%, "
                          f"个人持有 {personal_ratio:.2f}%, 规模：{fund_scale}亿元")

        except Exception:
            continue

    print()
    print("=" * 60)
    print(f"查找完成！共检查 {processed} 只基金")
    print(f"找到 {len(result)} 只机构持有占比 > {threshold}% 的基金")
    print("=" * 60)

    return result


def save_institution_funds(data: List[Dict], filename: str = None) -> Optional[Path]:
    """
    保存机构基金数据到 CSV

    Args:
        data: 数据列表
        filename: 文件名

    Returns:
        保存的文件路径
    """
    if not data:
        print("没有数据可保存")
        return None

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"institution_funds_{timestamp}.csv"

    output_dir = get_output_dir()
    filepath = output_dir / filename

    fieldnames = ["基金代码", "基金名称", "基金类型", "机构持有占比 (%)",
                  "个人持有占比 (%)", "基金规模 (亿元)"]

    try:
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"结果已保存到：{filepath}")
        return filepath
    except Exception as e:
        print(f"保存文件失败：{e}")
        return None
