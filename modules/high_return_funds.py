#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高收益股票型基金分析模块

筛选近 1 年收益率达到指定阈值的股票型基金。
"""

import csv
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from core.config import get_output_dir
from core.http_client import fetch_text, get_session
from core.tiantian_api import get_fund_list, get_fund_info


# 股票型基金类型关键词
STOCK_FUND_TYPES = ['股票型', '普通股票', '股票发起', '股票指数']


def is_stock_fund(fund_type: str) -> bool:
    """
    判断是否为股票型基金

    Args:
        fund_type: 基金类型字符串

    Returns:
        是否为股票型基金
    """
    if not fund_type:
        return False
    
    for keyword in STOCK_FUND_TYPES:
        if keyword in fund_type:
            return True
    return False


def get_fund_return_1y(fund_code: str) -> Optional[float]:
    """
    获取基金近 1 年收益率

    Args:
        fund_code: 基金代码

    Returns:
        近 1 年收益率（百分比数值，如 50.5 表示 50.5%）
    """
    url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
    headers = {
        "Referer": "http://fund.eastmoney.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        session = get_session()
        session.headers.update(headers)
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        content = resp.text

        # 提取近 1 年收益率 syl_1n
        match = re.search(r'syl_1n\s*=\s*"([^"]+)"', content)
        if match:
            return float(match.group(1))
        
        return None
        
    except Exception as e:
        return None


def search_high_return_funds(
    min_return: float = 50.0,
    target_count: int = 50,
    fund_type_filter: str = '股票型'
) -> List[Dict]:
    """
    搜索近 1 年收益率高于指定阈值的股票型基金

    Args:
        min_return: 最低收益率阈值（%），默认 50%
        target_count: 目标找到数量
        fund_type_filter: 基金类型过滤，默认'股票型'

    Returns:
        符合条件的基金列表
    """
    result = []

    print(f"开始查找近 1 年收益率 > {min_return}% 的{fund_type_filter}基金...")
    print(f"找到 {target_count} 只符合条件的基金后停止")
    print("-" * 80)

    fund_list = get_fund_list()
    if not fund_list:
        print("获取基金列表失败")
        return result

    processed = 0
    high_return_count = 0
    
    for fund in fund_list:
        if len(result) >= target_count:
            break

        try:
            fund_code = fund[0]
            fund_name = fund[1]
            fund_type = fund[2] if len(fund) > 2 else ""

            # 只处理股票型基金
            if fund_type_filter and not is_stock_fund(fund_type):
                continue

            processed += 1
            
            # 每处理 100 只显示一次进度
            if processed % 100 == 0:
                print(f"已处理 {processed} 只基金，找到 {high_return_count} 只高收益基金...")

            # 获取近 1 年收益率
            return_1y = get_fund_return_1y(fund_code)
            
            if return_1y is not None and return_1y >= min_return:
                high_return_count += 1
                
                fund_result = {
                    "基金代码": fund_code,
                    "基金名称": fund_name,
                    "基金类型": fund_type,
                    "近 1 年收益率 (%)": round(return_1y, 2),
                }
                result.append(fund_result)
                print(f"✓ [{fund_code}] {fund_name}: 近 1 年收益 {return_1y:.2f}% ({fund_type})")

        except Exception as e:
            continue

    print()
    print("=" * 80)
    print(f"查找完成！共检查 {processed} 只{fund_type_filter}基金")
    print(f"其中 {high_return_count} 只收益率 > {min_return}%")
    print(f"找到 {len(result)} 只符合条件的基金")
    print("=" * 80)

    return result


def save_high_return_funds(data: List[Dict], filename: str = None) -> Optional[Path]:
    """
    保存高收益基金数据到 CSV

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
        filename = f"high_return_funds_{timestamp}.csv"

    output_dir = get_output_dir()
    filepath = output_dir / filename

    fieldnames = ["基金代码", "基金名称", "基金类型", "近 1 年收益率 (%)"]

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


def print_summary(data: List[Dict]):
    """
    打印摘要信息

    Args:
        data: 基金列表
    """
    if not data:
        print("暂无数据")
        return

    print("\n" + "=" * 100)
    print("高收益股票型基金列表")
    print("=" * 100)
    print(f"{'序号':<4} {'基金代码':<10} {'基金名称':<25} {'基金类型':<20} {'近 1 年收益率':>12}")
    print("=" * 100)

    for i, fund in enumerate(data, 1):
        print(f"{i:<4} {fund['基金代码']:<10} {fund['基金名称']:<25} "
              f"{fund['基金类型']:<20} {fund['近 1 年收益率 (%)']:>11.2f}%")

    print("=" * 100)
    print(f"共 {len(data)} 只基金")
    
    if data:
        avg_return = sum(f['近 1 年收益率 (%)'] for f in data) / len(data)
        max_return = max(f['近 1 年收益率 (%)'] for f in data)
        min_return = min(f['近 1 年收益率 (%)'] for f in data)
        max_fund = max(data, key=lambda x: x['近 1 年收益率 (%)'])
        
        print(f"平均收益率：{avg_return:.2f}%")
        print(f"最高收益率：{max_return:.2f}% ({max_fund['基金名称']})")
        print(f"最低收益率：{min_return:.2f}%")
        print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)


class HighReturnFundFinder:
    """高收益基金发现器（类封装版本）"""

    def __init__(self, min_return: float = 50.0, target_count: int = 50):
        """
        初始化发现器

        Args:
            min_return: 最低收益率阈值（%）
            target_count: 目标找到数量
        """
        self.min_return = min_return
        self.target_count = target_count
        self.results: List[Dict] = []

    def find(self) -> List[Dict]:
        """执行查找"""
        self.results = search_high_return_funds(
            min_return=self.min_return,
            target_count=self.target_count
        )
        return self.results

    def print_results(self):
        """打印结果"""
        print_summary(self.results)

    def save(self, filename: str = None) -> Optional[Path]:
        """保存结果"""
        return save_high_return_funds(self.results, filename)

    def get_summary(self) -> Dict:
        """获取摘要"""
        if not self.results:
            return {}

        return {
            'count': len(self.results),
            'min_return': self.min_return,
            'avg_return': sum(f['近 1 年收益率 (%)'] for f in self.results) / len(self.results),
            'max_return': max(f['近 1 年收益率 (%)'] for f in self.results),
            'max_fund': max(self.results, key=lambda x: x['近 1 年收益率 (%)']),
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }


def find_high_return_stock_funds(min_return: float = 50.0,
                                  target_count: int = 50,
                                  save_csv: bool = True) -> List[Dict]:
    """
    便捷函数：查找高收益股票型基金

    Args:
        min_return: 最低收益率阈值（%）
        target_count: 目标找到数量
        save_csv: 是否保存 CSV

    Returns:
        符合条件的基金列表
    """
    finder = HighReturnFundFinder(min_return, target_count)
    finder.find()
    finder.print_results()

    if save_csv:
        finder.save()

    return finder.results


def find_high_return_funds(min_return: Optional[float] = None,
                           target_count: Optional[int] = None) -> List[Dict]:
    """
    便捷函数：查找高收益基金（支持参数覆盖配置）

    Args:
        min_return: 最低收益率阈值（%），None 时使用配置值
        target_count: 目标找到数量，None 时使用配置值

    Returns:
        符合条件的基金列表
    """
    from core.config import load_config

    config = load_config()
    hf_config = config.get('high_return_funds', {})

    # 参数优先，配置兜底
    if min_return is None:
        min_return = hf_config.get('min_return', 50.0)
    if target_count is None:
        target_count = hf_config.get('target_count', 50)

    finder = HighReturnFundFinder(min_return, target_count)
    finder.find()
    finder.print_results()
    finder.save()

    return finder.results
