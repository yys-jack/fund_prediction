#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP 客户端模块

提供统一的 HTTP 请求封装，管理请求头、超时等配置。
"""

import requests
from typing import Optional, Dict


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "http://fund.eastmoney.com/",
}

DEFAULT_TIMEOUT = 10


def get_session() -> requests.Session:
    """
    创建带默认配置的 Session

    Returns:
        配置好的 requests Session 对象
    """
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch_text(url: str, headers: Optional[Dict] = None, timeout: int = DEFAULT_TIMEOUT,
               encoding: str = 'utf-8') -> str:
    """
    获取 URL 内容并返回文本

    Args:
        url: 目标 URL
        headers: 额外的请求头
        timeout: 超时时间（秒）
        encoding: 响应编码

    Returns:
        响应文本内容，失败时返回空字符串
    """
    session = get_session()
    if headers:
        session.headers.update(headers)

    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        # 使用 content 解码，处理 BOM
        content = response.content.decode(encoding if encoding != 'utf-8-sig' else 'utf-8-sig')
        return content
    except requests.RequestException as e:
        print(f"请求失败 {url}: {e}")
        return ""


def fetch_json(url: str, headers: Optional[Dict] = None, timeout: int = DEFAULT_TIMEOUT,
               params: Optional[Dict] = None) -> Optional[dict]:
    """
    获取 URL 内容并解析为 JSON

    Args:
        url: 目标 URL
        headers: 额外的请求头
        timeout: 超时时间（秒）
        params: URL 查询参数

    Returns:
        解析后的字典，失败时返回 None
    """
    session = get_session()
    if headers:
        session.headers.update(headers)

    try:
        response = session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"请求失败 {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败 {url}: {e}")
        return None
