#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天天基金网基金重仓股票数据获取脚本

此脚本已重构，核心功能已移至 modules/fund_holdings.py
此文件保留用于向后兼容
"""

import json
from core import setup_utf8_stdout, get_fund_code
from modules.fund_holdings import FundHoldingsFetcher


def main():
    """主函数"""
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
