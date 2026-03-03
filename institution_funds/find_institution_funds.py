# -*- coding: utf-8 -*-
"""
查找机构持有占比高于 30% 的基金
使用天天基金网 API 获取基金持有人结构数据
"""

import sys
import io
import csv
import requests
import json
import re
from datetime import datetime
from pathlib import Path

# 设置标准输出为 UTF-8 编码，防止中文乱码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 设置输出目录为 output
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def get_fund_list() -> list:
    """获取所有基金代码列表"""
    url = "http://fund.eastmoney.com/js/fundcode_search.js"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://fund.eastmoney.com/fundjz.html",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        content = response.content.decode('utf-8-sig')
        match = content.replace("var r = ", "").replace(";", "").strip()
        fund_list = json.loads(match)
        print(f"获取到 {len(fund_list)} 只基金")
        return fund_list
    except Exception as e:
        print(f"获取基金列表失败：{e}")
        return []


def get_holder_structure(fund_code: str) -> dict:
    """获取基金持有人结构（机构/个人占比）"""
    url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"http://fund.eastmoney.com/{fund_code}.html",
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = 'utf-8'
        content = response.text

        pattern = r'Data_holderStructure\s*=\s*({.+?});'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            holder_data = json.loads(match.group(1))
            series = holder_data.get("series", [])
            categories = holder_data.get("categories", [])

            if series and categories:
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
        return None
    except Exception:
        return None


def get_fund_scale(fund_code: str) -> str:
    """获取基金规模（亿元）

    从天天基金网获取基金规模数据。
    使用 Data_fluctuationScale（基金规模波动）中的最新非零数据。
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "http://fund.eastmoney.com/",
    }

    try:
        # 从 pingzhongdata 获取 Data_fluctuationScale 数据
        psg_url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
        response = requests.get(psg_url, headers=headers, timeout=5)
        response.encoding = 'utf-8'
        content = response.text

        # 获取 Data_fluctuationScale 数据（基金规模波动）
        match = re.search(r'Data_fluctuationScale\s*=\s*({[^;]+});', content)
        if match:
            data = json.loads(match.group(1))
            categories = data.get("categories", [])
            series = data.get("series", [])

            if categories and series:
                # 获取最新的非零规模值
                # series 中的每个元素有 "y" (规模值) 和 "mom" (环比变化)
                values = [(cat, item.get("y", 0)) for cat, item in zip(categories, series)]
                # 过滤掉零值和空值，取最后一个有效值
                valid_values = [(cat, v) for cat, v in values if v and v > 0]
                if valid_values:
                    latest_cat, latest_scale = valid_values[-1]
                    return str(round(latest_scale, 2))

        return "N/A"
    except Exception:
        return "N/A"


def search_institution_funds(threshold: float = 30.0, target_count: int = 30) -> list:
    """搜索机构持有占比高于指定阈值的基金"""
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
                    print(f"✓ [{fund_code}] {fund_name}: 机构持有 {inst_ratio:.2f}%, 个人持有 {personal_ratio:.2f}%, 规模：{fund_scale}亿元")

        except Exception:
            continue

    print()
    print("=" * 60)
    print(f"查找完成！共检查 {processed} 只基金")
    print(f"找到 {len(result)} 只机构持有占比 > {threshold}% 的基金")
    print("=" * 60)

    return result


def save_to_csv(data: list, filename: str = None):
    """保存结果到 CSV 文件"""
    if not data:
        print("没有数据可保存")
        return

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"institution_funds_{timestamp}.csv"

    # 确保文件保存在 output 目录下
    filepath = OUTPUT_DIR / filename

    fieldnames = ["基金代码", "基金名称", "基金类型", "机构持有占比 (%)", "个人持有占比 (%)", "基金规模 (亿元)"]

    try:
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"结果已保存到：{filepath}")
    except Exception as e:
        print(f"保存文件失败：{e}")


def main():
    print("=" * 60)
    print("=== 基金机构持有占比筛选工具 ===")
    print("=" * 60)
    print()

    # 设置阈值和目标数量
    threshold = 30.0  # 机构持有占比高于 30%
    target_count = 100  # 找到 100 只就停止

    # 查找符合条件的基金
    result = search_institution_funds(threshold=threshold, target_count=target_count)

    # 显示结果
    if result:
        print()
        print("=== 符合条件的基金列表 ===")
        print("-" * 100)
        print(f"{'代码':<8} {'名称':<20} {'机构占比':>10} {'个人占比':>10} {'规模':>15}")
        print("-" * 100)

        # 按机构持有占比降序排列
        result.sort(key=lambda x: x["机构持有占比 (%)"], reverse=True)

        for fund in result:
            print(f"{fund['基金代码']:<8} {fund['基金名称']:<20} "
                  f"{fund['机构持有占比 (%)']:>10.2f}% {fund['个人持有占比 (%)']:>10.2f}% {str(fund['基金规模 (亿元)']):>15}")

        print("-" * 100)
        print(f"共 {len(result)} 只基金")

    # 保存到 CSV 文件
    save_to_csv(result)

if __name__ == "__main__":
    main()
