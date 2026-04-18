#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金持仓分析模块

获取基金的重仓股票数据和实时行情。
"""

import re
import json
from typing import List, Dict, Optional

from core.http_client import get_session, fetch_text, fetch_json


class FundHoldingsFetcher:
    """基金重仓股票数据获取器"""

    def __init__(self, fund_code: str):
        """
        初始化获取器

        Args:
            fund_code: 基金代码，如 '161725'
        """
        self.fund_code = fund_code
        self.headers = {
            "Referer": "http://fund.eastmoney.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.fund_info = {}
        self.stock_codes = []
        self.stock_details = []

    def fetch_fund_data(self) -> bool:
        """
        获取基金数据（持仓股票代码、基金名称等）

        Returns:
            bool: 是否成功获取
        """
        url = f"http://fund.eastmoney.com/pingzhongdata/{self.fund_code}.js"
        try:
            session = get_session()
            session.headers.update(self.headers)
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
            content = resp.text

            # 提取基金基本信息
            fund_name_match = re.search(r'fS_name\s*=\s*"([^"]+)"', content)
            if fund_name_match:
                self.fund_info['name'] = fund_name_match.group(1)

            self.fund_info['code'] = self.fund_code

            # 提取收益率
            syl_fields = {
                'syl_1n': 'return_1y',
                'syl_6y': 'return_6m',
                'syl_3y': 'return_3m',
                'syl_1y': 'return_1m',
            }

            for js_field, info_field in syl_fields.items():
                match = re.search(rf'{js_field}\s*=\s*"([^"]+)"', content)
                if match:
                    self.fund_info[info_field] = f"{match.group(1)}%"

            # 提取股票持仓代码（格式：1.600519）
            stock_codes = re.findall(r'"([01]\.\d{6})"', content)

            # 过滤掉债券代码
            self.stock_codes = []
            for code in stock_codes:
                market, sec_code = code.split('.')
                if not re.match(r'1[12][378]\d{3}', sec_code):
                    self.stock_codes.append(code)

            print(f"基金：{self.fund_info.get('name', 'Unknown')} ({self.fund_code})")
            print(f"持仓股票数量：{len(self.stock_codes)}")
            return True

        except Exception as e:
            print(f"获取基金数据失败：{e}")
            return False

    def fetch_stock_details(self) -> List[Dict]:
        """
        获取持仓股票的详细信息

        Returns:
            List[Dict]: 股票详情列表
        """
        if not self.stock_codes:
            print("请先调用 fetch_fund_data() 获取股票列表")
            return []

        self.stock_details = []
        session = get_session()
        session.headers.update(self.headers)

        for code in self.stock_codes:
            market, sec_code = code.split('.')
            url = f"http://push2.eastmoney.com/api/qt/stock/get?fltt=2&secid={code}"

            try:
                resp = session.get(url, timeout=10)
                data = json.loads(resp.text)

                if data.get('data'):
                    s = data['data']
                    price = s.get('f43', 0)
                    prev_close = s.get('f46', 0)
                    change = price - prev_close if prev_close else 0
                    change_pct = (change / prev_close * 100) if prev_close else 0

                    stock_info = {
                        'code': s.get('f57', sec_code),
                        'name': s.get('f58', 'Unknown'),
                        'price': price,
                        'change': change,
                        'change_pct': change_pct,
                        'prev_close': prev_close,
                        'volume': s.get('f47', 0),
                        'turnover': s.get('f48', 0),
                        'market': 'SH' if market == '1' else 'SZ',
                        'fund_code_format': code
                    }
                    self.stock_details.append(stock_info)

            except Exception as e:
                print(f"获取股票 {code} 数据失败：{e}")
                continue

        return self.stock_details

    def get_holdings(self) -> List[Dict]:
        """
        获取持仓数据（链式调用便捷方法）

        Returns:
            持仓股票详情列表
        """
        if self.fetch_fund_data():
            return self.fetch_stock_details()
        return []

    def print_holdings(self):
        """打印持仓股票信息"""
        if not self.stock_details:
            print("暂无股票数据")
            return

        print(f"\n{'='*80}")
        print(f"基金：{self.fund_info.get('name', 'Unknown')} ({self.fund_code})")
        print(f"近一年收益：{self.fund_info.get('return_1y', 'N/A')}")
        print(f"{'='*80}")
        print(f"{'序号':<4} {'代码':<8} {'名称':<12} {'现价':>10} {'涨跌额':>8} {'涨幅%':>8} {'成交量 (手)':>12}")
        print(f"{'='*80}")

        for i, stock in enumerate(self.stock_details, 1):
            print(f"{i:<4} {stock['code']:<8} {stock['name']:<12} "
                  f"{stock['price']:>10.2f} {stock['change']:>8.2f} "
                  f"{stock['change_pct']:>8.2f} {stock['volume']:>12.0f}")

        print(f"{'='*80}")
        print(f"持仓股票总数：{len(self.stock_details)}")

    def to_dataframe(self):
        """
        返回 DataFrame 格式（需要 pandas）

        Returns:
            pd.DataFrame or None: 持仓数据 DataFrame
        """
        try:
            import pandas as pd
            if self.stock_details:
                return pd.DataFrame(self.stock_details)
            return None
        except ImportError:
            print("需要安装 pandas: pip install pandas")
            return None
