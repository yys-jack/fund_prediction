#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热门股票分析脚本

通过分析多只基金的持仓数据，找出被最多基金共同持有的热门股票。

使用方法：
    python scripts/find_popular_stocks.py

配置：
    在 config.json 中配置 fund_codes 列表和 top_count
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.popular_stocks import PopularStocksFinder, find_popular_stocks


def load_config() -> dict:
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config.json"
    
    if not config_path.exists():
        print(f"配置文件不存在：{config_path}")
        print("请复制 config.json.example 为 config.json 并配置基金代码列表")
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """主函数"""
    print("=" * 60)
    print("=== 热门股票分析工具 ===")
    print("=" * 60)
    print()
    
    # 加载配置
    config = load_config()
    if not config:
        return
    
    # 获取热门股票分析配置
    popular_config = config.get('popular_stocks', {})
    fund_codes = popular_config.get('fund_codes', [])
    top_count = popular_config.get('top_count', 30)
    
    if not fund_codes:
        # 如果没有配置 popular_stocks，尝试使用 fund_codes
        fund_codes = config.get('fund_codes', ['161725'])
    
    print(f"配置信息:")
    print(f"  分析基金数量：{len(fund_codes)}")
    print(f"  热门股票数量：{top_count}")
    print()
    
    if len(fund_codes) < 3:
        print("⚠️  警告：建议至少分析 3 只基金以获得有意义的结果")
        print()
    
    # 执行分析
    finder = PopularStocksFinder(fund_codes, top_count)
    finder.analyze()
    finder.print_results()
    
    # 保存 CSV
    finder.to_csv()
    
    # 打印摘要
    summary = finder.get_summary()
    if summary:
        print("\n=== 分析摘要 ===")
        print(f"  分析基金数量：{summary['fund_count']}")
        print(f"  发现股票总数：{summary['total_stocks']}")
        print(f"  热门股票数量：{summary['top_stocks_count']}")
        print(f"  平均持有基金数：{summary['avg_fund_count']:.2f}")
        print(f"  最受欢迎股票：{summary['most_popular_stock']['股票代码']} "
              f"{summary['most_popular_stock']['股票名称']} "
              f"({summary['most_popular_stock']['持有基金数']} 只基金持有)")
        print(f"  分析时间：{summary['analysis_time']}")


if __name__ == "__main__":
    main()
