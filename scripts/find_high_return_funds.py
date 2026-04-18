#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高收益股票型基金筛选脚本

筛选近 1 年收益率达到指定阈值的股票型基金。

使用方法：
    python scripts/find_high_return_funds.py

配置：
    在 config.json 中配置 high_return_funds 相关参数
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.high_return_funds import HighReturnFundFinder, find_high_return_stock_funds


def load_config() -> dict:
    """加载配置文件"""
    config_path = project_root / "config.json"
    
    if not config_path.exists():
        print(f"配置文件不存在：{config_path}")
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """主函数"""
    print("=" * 80)
    print("=== 高收益股票型基金筛选工具 ===")
    print("=" * 80)
    print()
    
    # 加载配置
    config = load_config()
    if not config:
        # 使用默认配置
        min_return = 50.0
        target_count = 50
    else:
        high_return_config = config.get('high_return_funds', {})
        min_return = high_return_config.get('min_return', 50.0)
        target_count = high_return_config.get('target_count', 50)
    
    print(f"配置信息:")
    print(f"  最低收益率：{min_return}%")
    print(f"  目标数量：{target_count} 只")
    print(f"  基金类型：股票型")
    print()
    
    # 执行分析
    finder = HighReturnFundFinder(min_return, target_count)
    finder.find()
    finder.print_results()
    
    # 保存 CSV
    finder.save()
    
    # 打印摘要
    summary = finder.get_summary()
    if summary:
        print("\n=== 分析摘要 ===")
        print(f"  筛选条件：近 1 年收益率 > {summary['min_return']}%")
        print(f"  找到基金数量：{summary['count']}")
        print(f"  平均收益率：{summary['avg_return']:.2f}%")
        print(f"  最高收益率：{summary['max_return']:.2f}% "
              f"({summary['max_fund']['基金名称']})")
        print(f"  分析时间：{summary['analysis_time']}")


if __name__ == "__main__":
    main()
