#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金持仓股票分析脚本

获取基金的重仓股票数据和实时行情。
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import setup_utf8_stdout, get_fund_code
from modules.fund_holdings import FundHoldingsFetcher


def main():
    setup_utf8_stdout()
    fund_code = get_fund_code()

    print(f"使用基金代码：{fund_code}")

    fetcher = FundHoldingsFetcher(fund_code)

    # 获取基金数据
    if fetcher.fetch_fund_data():
        # 获取股票详情
        fetcher.fetch_stock_details()
        # 打印结果
        fetcher.print_holdings()
        # 保存到 JSON
        filename = f"fund_{fund_code}_holdings.json"
        data = {
            'fund_info': fetcher.fund_info,
            'holdings': fetcher.stock_details
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到：{filename}")


if __name__ == "__main__":
    main()
