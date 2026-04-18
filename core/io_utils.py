#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输入输出工具模块

提供 CSV/JSON 文件保存、标准输出编码设置等功能。
"""

import csv
import json
import sys
import io
from pathlib import Path
from typing import List, Dict, Optional

from .config import get_output_dir


def setup_utf8_stdout():
    """
    设置标准输出为 UTF-8 编码，防止中文乱码
    """
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def save_to_csv(data: List[Dict], filename: str, fieldnames: Optional[List[str]] = None) -> Optional[Path]:
    """
    保存数据到 CSV 文件

    Args:
        data: 数据列表（字典列表）
        filename: 文件名
        fieldnames: 字段名列表，如不提供则从数据中自动提取

    Returns:
        保存的文件路径，失败时返回 None
    """
    if not data:
        print("没有数据可保存")
        return None

    output_dir = get_output_dir()
    filepath = output_dir / filename

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    try:
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(f"数据已保存到：{filepath}")
        return filepath
    except Exception as e:
        print(f"保存文件失败：{e}")
        return None


def save_to_json(data: Dict, filename: str) -> Optional[Path]:
    """
    保存数据到 JSON 文件

    Args:
        data: 数据字典
        filename: 文件名

    Returns:
        保存的文件路径，失败时返回 None
    """
    output_dir = get_output_dir()
    filepath = output_dir / filename

    try:
        with open(filepath, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"数据已保存到：{filepath}")
        return filepath
    except Exception as e:
        print(f"保存文件失败：{e}")
        return None
