"""
Fund Prediction - 核心模块

提供配置管理、HTTP 客户端、数据输入输出等共享功能。
"""

from .config import load_config, get_fund_code, get_fund_codes, get_output_dir, get_project_root
from .http_client import get_session, fetch_text, fetch_json
from .io_utils import save_to_csv, save_to_json, setup_utf8_stdout

__all__ = [
    'load_config',
    'get_fund_code',
    'get_fund_codes',
    'get_output_dir',
    'get_project_root',
    'get_session',
    'fetch_text',
    'fetch_json',
    'save_to_csv',
    'save_to_json',
    'setup_utf8_stdout',
]
