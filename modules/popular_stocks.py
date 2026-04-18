#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热门股票分析模块

通过分析多只基金的持仓数据，统计每只股票被多少只基金持有，
找出被最多基金共同持有的热门股票。
"""

import json
import csv
import re
from collections import defaultdict
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from core.http_client import get_session, fetch_json
from core.tiantian_api import get_stock_codes, get_fund_info


def load_fund_pool(csv_path: str) -> List[str]:
    """
    从 CSV 文件读取基金代码列表

    Args:
        csv_path: 基金池 CSV 文件路径

    Returns:
        基金代码列表
    """
    fund_codes = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get('基金代码', '').strip()
            if code:
                fund_codes.append(code)
    return fund_codes


class PopularStocksFinder:
    """热门股票发现器"""

    def __init__(self, fund_codes: Optional[List[str]] = None,
                 top_count: int = 30,
                 fund_pool_csv: Optional[str] = None):
        """
        初始化发现器

        Args:
            fund_codes: 要分析的基金代码列表，与 fund_pool_csv 二选一
            top_count: 返回的热门股票数量，默认 30
            fund_pool_csv: 基金池 CSV 文件路径，与 fund_codes 二选一
        """
        # 支持从 CSV 读取基金池
        if fund_pool_csv:
            self.fund_codes = load_fund_pool(fund_pool_csv)
        elif fund_codes:
            self.fund_codes = fund_codes
        else:
            self.fund_codes = []

        self.top_count = top_count
        self.headers = {
            "Referer": "http://fund.eastmoney.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        # 存储每只股票被哪些基金持有
        self.stock_funds: Dict[str, List[str]] = defaultdict(list)
        # 存储股票热度统计
        self.stock_heat: List[Dict] = []
        # 存储股票详细信息
        self.stock_details: List[Dict] = []

    def fetch_all_holdings(self) -> int:
        """
        获取所有基金的重仓股票

        Returns:
            成功获取的基金数量
        """
        session = get_session()
        session.headers.update(self.headers)
        success_count = 0

        print(f"开始获取 {len(self.fund_codes)} 只基金的持仓数据...")
        print("-" * 60)

        for i, fund_code in enumerate(self.fund_codes, 1):
            try:
                # 获取基金持仓股票代码
                stocks = get_stock_codes(fund_code)
                
                if stocks:
                    fund_name = get_fund_info(fund_code).get('name', 'Unknown')
                    print(f"[{i}/{len(self.fund_codes)}] {fund_code} - {fund_name}: {len(stocks)} 只股票")
                    
                    # 记录每只股票被哪些基金持有
                    for stock in stocks:
                        stock_code = stock['code']
                        self.stock_funds[stock_code].append(fund_code)
                    
                    success_count += 1
                else:
                    print(f"[{i}/{len(self.fund_codes)}] {fund_code}: 未获取到持仓数据")
                    
            except Exception as e:
                print(f"[{i}/{len(self.fund_codes)}] {fund_code}: 获取失败 - {e}")
                continue

        print("-" * 60)
        print(f"成功获取 {success_count}/{len(self.fund_codes)} 只基金的持仓数据")
        print(f"共发现 {len(self.stock_funds)} 只不同的股票")
        
        return success_count

    def calculate_heat(self) -> List[Dict]:
        """
        计算股票热度（被多少只基金持有）

        Returns:
            按热度排序的股票列表
        """
        if not self.stock_funds:
            print("请先调用 fetch_all_holdings() 获取持仓数据")
            return []

        print("\n计算股票热度...")
        
        # 构建热度列表
        self.stock_heat = []
        for stock_code, fund_list in self.stock_funds.items():
            self.stock_heat.append({
                'stock_code': stock_code,
                'fund_count': len(fund_list),
                'fund_codes': fund_list,
            })
        
        # 按持有基金数量降序排序
        self.stock_heat.sort(key=lambda x: x['fund_count'], reverse=True)
        
        # 取前 N 只热门股票
        top_stocks = self.stock_heat[:self.top_count]
        
        print(f"前 {len(top_stocks)} 只热门股票:")
        for i, stock in enumerate(top_stocks[:10], 1):
            print(f"  {i}. {stock['stock_code']}: {stock['fund_count']} 只基金持有")
        if len(top_stocks) > 10:
            print(f"  ... 还有 {len(top_stocks) - 10} 只")
        
        return top_stocks

    def fetch_stock_details(self, stock_list: Optional[List[Dict]] = None) -> List[Dict]:
        """
        获取热门股票的详细信息

        Args:
            stock_list: 股票列表，如果为 None 则使用热度前 top_count 只

        Returns:
            包含详细信息的股票列表
        """
        if stock_list is None:
            stock_list = self.stock_heat[:self.top_count]
        
        if not stock_list:
            print("没有股票数据可获取详情")
            return []

        print(f"\n获取 {len(stock_list)} 只热门股票的详细信息...")
        
        self.stock_details = []
        session = get_session()
        session.headers.update(self.headers)

        for i, stock in enumerate(stock_list):
            stock_code = stock['stock_code']
            
            # 过滤非 A 股代码（美股、港股、债券等）
            # A 股代码格式：60xxxx, 000xxx, 002xxx, 300xxx, 688xxx(科创板)
            if not re.match(r'^(60|000|002|300|688)\d{4}$', stock_code):
                # 非 A 股，添加基本信息但不获取行情
                self.stock_details.append({
                    '序号': i + 1,
                    '股票代码': stock_code,
                    '股票名称': 'Unknown (非 A 股)',
                    '现价': 0,
                    '涨跌额': 0,
                    '涨幅%': 0,
                    '成交量 (手)': 0,
                    '成交额 (元)': 0,
                    '持有基金数': stock['fund_count'],
                    '持有基金代码': ','.join(stock['fund_codes'][:5]),
                })
                continue
            
            # 判断市场
            market = '1' if stock_code.startswith('6') else '0'
            secid = f"{market}.{stock_code}"
            
            url = f"http://push2.eastmoney.com/api/qt/stock/get?fltt=2&secid={secid}"
            
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
                        '序号': i + 1,
                        '股票代码': stock_code,
                        '股票名称': s.get('f58', 'Unknown'),
                        '现价': price,
                        '涨跌额': change,
                        '涨幅%': change_pct,
                        '成交量 (手)': s.get('f47', 0),
                        '成交额 (元)': s.get('f48', 0),
                        '持有基金数': stock['fund_count'],
                        '持有基金代码': ','.join(stock['fund_codes'][:5]),  # 只显示前 5 个
                    }
                    
                    if len(stock['fund_codes']) > 5:
                        stock_info['持有基金代码'] += f"...(+{len(stock['fund_codes']) - 5})"
                    
                    self.stock_details.append(stock_info)
                    
            except Exception as e:
                print(f"获取股票 {stock_code} 详情失败：{e}")
                # 添加基本信息
                self.stock_details.append({
                    '序号': i + 1,
                    '股票代码': stock_code,
                    '股票名称': 'Unknown',
                    '现价': 0,
                    '涨跌额': 0,
                    '涨幅%': 0,
                    '成交量 (手)': 0,
                    '成交额 (元)': 0,
                    '持有基金数': stock['fund_count'],
                    '持有基金代码': ','.join(stock['fund_codes'][:5]),
                })
                continue

        print(f"成功获取 {len([s for s in self.stock_details if s['股票名称'] != 'Unknown'])} 只股票详情")
        return self.stock_details

    def analyze(self) -> List[Dict]:
        """
        执行完整分析流程（链式调用）

        Returns:
            热门股票详情列表
        """
        if self.fetch_all_holdings() > 0:
            self.calculate_heat()
            return self.fetch_stock_details()
        return []

    def print_results(self):
        """打印分析结果"""
        if not self.stock_details:
            print("暂无分析结果")
            return

        print("\n" + "=" * 120)
        print("热门股票分析结果")
        print("=" * 120)
        print(f"{'序号':<4} {'股票代码':<10} {'股票名称':<12} {'现价':>10} {'涨幅%':>8} {'持有基金数':>12} {'持有基金'}")
        print("=" * 120)

        for stock in self.stock_details:
            print(f"{stock['序号']:<4} {stock['股票代码']:<10} {stock['股票名称']:<12} "
                  f"{stock['现价']:>10.2f} {stock['涨幅%']:>8.2f} {stock['持有基金数']:>12} {stock['持有基金代码']}")

        print("=" * 120)
        print(f"分析基金数量：{len(self.fund_codes)}")
        print(f"热门股票数量：{len(self.stock_details)}")
        print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def to_csv(self, filename: Optional[str] = None) -> str:
        """
        保存结果到 CSV 文件

        Args:
            filename: 文件名，如果为 None 则自动生成

        Returns:
            保存的文件路径
        """
        import csv
        from pathlib import Path
        
        if not self.stock_details:
            print("没有数据可保存")
            return ""

        # 确保输出目录存在
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"popular_stocks_{timestamp}.csv"

        filepath = output_dir / filename
        
        fieldnames = ['序号', '股票代码', '股票名称', '现价', '涨跌额', '涨幅%', 
                      '成交量 (手)', '成交额 (元)', '持有基金数', '持有基金代码']

        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.stock_details)
            
            print(f"\n结果已保存到：{filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"保存文件失败：{e}")
            return ""

    def get_summary(self) -> Dict:
        """
        获取分析摘要

        Returns:
            摘要信息字典
        """
        if not self.stock_details:
            return {}

        return {
            'fund_count': len(self.fund_codes),
            'total_stocks': len(self.stock_funds),
            'top_stocks_count': len(self.stock_details),
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'most_popular_stock': self.stock_details[0] if self.stock_details else None,
            'avg_fund_count': sum(s['持有基金数'] for s in self.stock_details) / len(self.stock_details) if self.stock_details else 0,
        }


def find_popular_stocks(fund_codes: List[str], top_count: int = 30, 
                        save_csv: bool = True) -> List[Dict]:
    """
    便捷函数：查找热门股票

    Args:
        fund_codes: 基金代码列表
        top_count: 返回的热门股票数量
        save_csv: 是否保存 CSV

    Returns:
        热门股票详情列表
    """
    finder = PopularStocksFinder(fund_codes, top_count)
    finder.analyze()
    finder.print_results()
    
    if save_csv:
        finder.to_csv()
    
    return finder.stock_details
