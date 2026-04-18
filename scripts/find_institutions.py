#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机构持有基金筛选脚本

查找机构持有占比高于指定阈值的基金。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import setup_utf8_stdout, load_config
from modules.institution_analysis import search_institution_funds, save_institution_funds


def main():
    setup_utf8_stdout()

    # 从配置文件加载参数
    config = load_config()
    inst_config = config.get('institution_fund', {})
    threshold = inst_config.get('threshold', 30.0)
    target_count = inst_config.get('target_count', 100)

    print("=" * 60)
    print("=== 基金机构持有占比筛选工具 ===")
    print("=" * 60)
    print()

    # 查找符合条件的基金
    result = search_institution_funds(threshold=threshold, target_count=target_count)

    # 显示结果
    if result:
        print()
        print("=== 符合条件的基金列表 ===")
        print("-" * 100)
        print(f"{'代码':<8} {'名称':<20} {'机构占比':>10} {'个人占比':>10} {'规模':>15}")
        print("-" * 100)

        # 按机构持有占比降序排列
        result.sort(key=lambda x: x["机构持有占比 (%)"], reverse=True)

        for fund in result:
            print(f"{fund['基金代码']:<8} {fund['基金名称']:<20} "
                  f"{fund['机构持有占比 (%)']:>10.2f}% {fund['个人持有占比 (%)']:>10.2f}% "
                  f"{str(fund['基金规模 (亿元)']):>15}")

        print("-" * 100)
        print(f"共 {len(result)} 只基金")

    # 保存到 CSV
    save_institution_funds(result)


if __name__ == "__main__":
    main()
