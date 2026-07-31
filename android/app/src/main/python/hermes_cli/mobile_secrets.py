"""移动端密钥安全解析。

配置文件中不再保存明文 API 密钥：
- 保存时写入占位符 ``__keystore__``（真实密钥由 Android Keystore 加密保管）
- 运行时由 Java 侧解密后注入环境变量 ``HERMES_MOBILE_API_KEY``
- 读取处通过 :func:`resolve_api_key` 把占位符解析为真实密钥

这样磁盘上任何配置文件都不含明文密钥。
"""
from __future__ import annotations

import os

KEYSTORE_PLACEHOLDER = "__keystore__"
ENV_KEY = "HERMES_MOBILE_API_KEY"


def resolve_api_key(value: str | None = "") -> str:
    """把配置里的密钥字段解析为真实密钥。

    占位符 ``__keystore__`` 表示密钥由移动端 Keystore 保管，运行时从
    环境变量 ``HERMES_MOBILE_API_KEY`` 读取；其余情况原样返回。
    """
    v = str(value or "").strip()
    if v == KEYSTORE_PLACEHOLDER:
        return os.environ.get(ENV_KEY, "").strip()
    return v


def is_placeholder(value: str | None = "") -> bool:
    """判断配置值是否为移动端密钥占位符。"""
    return str(value or "").strip() == KEYSTORE_PLACEHOLDER


def has_secure_key() -> bool:
    """运行时是否存在由 Keystore 注入的密钥。"""
    return bool(os.environ.get(ENV_KEY, "").strip())
