#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金筛选流程主脚本

步骤 1: 获取机构持有基金 + 高收益基金，合并去重
步骤 2: 分析热门股票
"""

import argparse
import sys
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.institution_analysis import search_institution_funds
from modules.high_return_funds import find_high_return_funds
from modules.popular_stocks import PopularStocksFinder, load_fund_pool
from core.io_utils import get_output_dir


def merge_funds(institutions: List[Dict], high_returns: List[Dict]) -> List[Dict]:
    """
    合并两个基金列表，去重并标记来源

    Args:
        institutions: 机构持有基金列表
        high_returns: 高收益基金列表

    Returns:
        合并后的基金池列表
    """
    fund_dict: Dict[str, Dict] = {}

    # 添加机构持有基金
    for fund in institutions:
        code = fund.get('基金代码', '')
        if code:
            fund_dict[code] = {
                '基金代码': code,
                '基金名称': fund.get('基金名称', ''),
                '来源标签': '机构',
                '近 1 年收益率': 'N/A',
                '机构持有占比': f"{fund.get('机构持有占比 (%)', 'N/A')}%" if isinstance(fund.get('机构持有占比 (%)'), (int, float)) else fund.get('机构持有占比 (%)', 'N/A'),
                '基金规模 (亿元)': fund.get('基金规模 (亿元)', 'N/A'),
            }

    # 添加高收益基金，处理重复
    for fund in high_returns:
        code = fund.get('基金代码', '')
        if code:
            if code in fund_dict:
                # 重复基金，更新标签
                fund_dict[code]['来源标签'] = '重复'
                # 更新收益率（高收益基金有收益率数据）
                fund_dict[code]['近 1 年收益率'] = f"{fund.get('近 1 年收益率 (%)', 'N/A')}%" if isinstance(fund.get('近 1 年收益率 (%)'), (int, float)) else fund.get('近 1 年收益率 (%)', 'N/A')
            else:
                fund_dict[code] = {
                    '基金代码': code,
                    '基金名称': fund.get('基金名称', ''),
                    '来源标签': '高收益',
                    '近 1 年收益率': f"{fund.get('近 1 年收益率 (%)', 'N/A')}%" if isinstance(fund.get('近 1 年收益率 (%)'), (int, float)) else fund.get('近 1 年收益率 (%)', 'N/A'),
                    '机构持有占比': 'N/A',
                    '基金规模 (亿元)': fund.get('基金规模', 'N/A'),
                }

    return list(fund_dict.values())


def save_fund_pool_to_csv(fund_pool: List[Dict], output_path: str):
    """
    保存基金池到 CSV

    Args:
        fund_pool: 基金池列表
        output_path: 输出文件路径
    """
    if not fund_pool:
        return

    headers = ['基金代码', '基金名称', '来源标签', '近 1 年收益率',
               '机构持有占比', '基金规模 (亿元)']

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for fund in fund_pool:
            writer.writerow(fund)


def run_step1(timestamp: str) -> str:
    """
    步骤 1: 获取机构持有基金和高收益基金，合并去重

    Args:
        timestamp: 时间戳字符串

    Returns:
        基金池 CSV 文件路径
    """
    print("[步骤 1/2] 获取机构持有基金...")
    institutions = search_institution_funds(threshold=30.0, target_count=50)
    print(f"  → 完成 ({len(institutions)} 只)")

    print("[步骤 1/2] 获取高收益基金 (≥30%)...")
    high_returns = find_high_return_funds(min_return=30.0, target_count=50)
    print(f"  → 完成 ({len(high_returns)} 只)")

    # 合并去重
    print("[步骤 1/2] 合并去重...")
    fund_pool = merge_funds(institutions, high_returns)

    # 统计来源标签
    inst_count = sum(1 for f in fund_pool if f['来源标签'] == '机构')
    high_count = sum(1 for f in fund_pool if f['来源标签'] == '高收益')
    dup_count = sum(1 for f in fund_pool if f['来源标签'] == '重复')
    print(f"  → 完成 (共 {len(fund_pool)} 只，机构 {inst_count} 只，高收益 {high_count} 只，重复 {dup_count} 只)")

    # 保存
    output_dir = get_output_dir()
    output_path = f"{output_dir}/fund_pool_{timestamp}.csv"
    save_fund_pool_to_csv(fund_pool, output_path)
    print(f"→ 已保存：{output_path}")

    return output_path


def run_step2(fund_pool_path: str, top_stocks: int, timestamp: str):
    """
    步骤 2: 分析热门股票

    Args:
        fund_pool_path: 基金池 CSV 文件路径
        top_stocks: 热门股票数量
        timestamp: 时间戳字符串
    """
    print(f"[步骤 2/2] 从 {fund_pool_path} 读取基金池...")
    fund_codes = load_fund_pool(fund_pool_path)
    print(f"  → 共 {len(fund_codes)} 只基金")

    print(f"[步骤 2/2] 分析热门股票 (前 {top_stocks} 只)...")
    finder = PopularStocksFinder(fund_codes=fund_codes, top_count=top_stocks)
    finder.analyze()

    output_dir = get_output_dir()
    output_path = f"{output_dir}/popular_stocks_{timestamp}.csv"
    finder.to_csv(output_path)
    print(f"→ 已保存：{output_path}")

    # 打印摘要
    summary = finder.get_summary()
    if summary.get('most_popular_stock'):
        stock = summary['most_popular_stock']
        print(f"\n最受欢迎股票：{stock.get('股票名称')} ({stock.get('股票代码')})")
        print(f"  被 {stock.get('持有基金数')} 只基金持有")


def main():
    parser = argparse.ArgumentParser(description='基金筛选流程')
    parser.add_argument('--step', type=int, choices=[1, 2], default=0,
                        help='只执行指定步骤 (1 或 2)，默认执行全部')
    parser.add_argument('--fund-pool', type=str,
                        help='步骤 2 使用的基金池 CSV 路径')
    parser.add_argument('--top-stocks', type=int, default=50,
                        help='热门股票数量，默认 50')
    args = parser.parse_args()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if args.step in (0, 1):
        fund_pool_path = run_step1(timestamp)
        if args.step == 0:
            run_step2(fund_pool_path, args.top_stocks, timestamp)
    else:
        if not args.fund_pool:
            print("错误：执行步骤 2 需指定 --fund-pool")
            sys.exit(1)
        run_step2(args.fund_pool, args.top_stocks, timestamp)


if __name__ == '__main__':
    main()
