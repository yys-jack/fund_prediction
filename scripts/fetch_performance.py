#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金业绩走势分析脚本

获取指定基金的近 1 年收益走势数据，保存到 CSV 文件。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import setup_utf8_stdout, get_fund_code
from modules.fund_performance import fetch_fund_performance, save_performance_to_csv


def main():
    setup_utf8_stdout()
    fund_code = get_fund_code()

    print(f"正在获取基金 {fund_code} 的数据...")
    print(f"获取近 1 年的收益走势数据")
    print()

    # 获取业绩数据
    result_data = fetch_fund_performance(fund_code)

    if not result_data:
        print("未能获取到基金数据")
        return

    # 保存到 CSV
    output_file = f"fund_{fund_code}_1year.csv"
    save_performance_to_csv(result_data, fund_code, output_file)

    # 打印摘要信息
    if result_data:
        print("\n" + "=" * 50)
        print("=== 收益走势摘要 ===")
        print("=" * 50)
        print(f"最早日期：{result_data[0]['日期']}")
        print(f"最新日期：{result_data[-1]['日期']}")
        print(f"起始单位净值：{result_data[0]['单位净值']}")
        print(f"起始累计净值：{result_data[0]['累计净值']}")
        print(f"最新单位净值：{result_data[-1]['单位净值']}")
        print(f"最新累计净值：{result_data[-1]['累计净值']}")
        print(f"累计收益率：{result_data[-1]['累计收益率 (%)']}%")
        print("=" * 50)


if __name__ == "__main__":
    main()
