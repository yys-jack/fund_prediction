#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

从 config.json 加载项目配置，提供统一的配置访问接口。
"""

import json
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def load_config() -> dict:
    """
    从配置文件加载配置

    Returns:
        包含完整配置的字典

    Raises:
        FileNotFoundError: 当 config.json 不存在时使用默认配置
    """
    config_path = get_project_root() / 'config.json'

    if not config_path.exists():
        print(f"警告：配置文件 {config_path} 不存在，将使用默认配置")
        return {
            "fund_code": "161725",
            "fund_codes": ["161725"],
            "institution_fund": {
                "threshold": 30.0,
                "target_count": 100
            }
        }

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_fund_code() -> str:
    """
    获取默认基金代码

    Returns:
        基金代码字符串
    """
    config = load_config()
    return config.get('fund_code', '161725')


def get_fund_codes() -> list:
    """
    获取基金代码列表

    Returns:
        基金代码列表
    """
    config = load_config()
    return config.get('fund_codes', ['161725'])


def get_output_dir() -> Path:
    """
    获取输出目录

    Returns:
        输出目录 Path 对象
    """
    output_dir = get_project_root() / 'output'
    output_dir.mkdir(exist_ok=True)
    return output_dir


def get_institution_config() -> dict:
    """
    获取机构基金分析配置

    Returns:
        包含 threshold 和 target_count 的字典
    """
    config = load_config()
    return config.get('institution_fund', {
        'threshold': 30.0,
        'target_count': 100
    })
