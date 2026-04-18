"""
Fund Prediction - 功能模块

提供基金业绩分析、持仓分析、机构持有分析等功能。
"""

from .popular_stocks import PopularStocksFinder, find_popular_stocks, load_fund_pool

__all__ = ['PopularStocksFinder', 'find_popular_stocks', 'load_fund_pool']
