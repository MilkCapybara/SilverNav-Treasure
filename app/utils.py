"""工具函数模块"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


def _serialize_value(value: Any) -> Any:
    """序列化单个值"""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _serialize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """序列化多行数据"""
    serialized = []
    for row in rows:
        serialized.append({k: _serialize_value(v) for k, v in row.items()})
    return serialized


def _serialize_row(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """序列化单行数据"""
    if not row:
        return {}
    return {k: _serialize_value(v) for k, v in row.items()}
