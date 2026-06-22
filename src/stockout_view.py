"""售罄预测视图：按预计售罄日排序（假设完全不补货）。"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pandas as pd

STOCKOUT_ONLY_COLS = [
    "商品名称",
    "SKU",
    "当前库存",
    "日均销量(加权)",
    "库存可售天数",
    "预计售罄日",
]

STOCKOUT_FULL_COLS = STOCKOUT_ONLY_COLS + ["建议进货量", "优先级"]


def build_stockout_view(df: pd.DataFrame, *, include_reorder: bool = True) -> pd.DataFrame:
    """按预计售罄日升序排列（最早卖完的在前，无法估算的排最后）。"""
    if df.empty or "预计售罄日" not in df.columns:
        return pd.DataFrame()

    view = df.copy()
    view["_stockout_sort"] = pd.to_datetime(view["预计售罄日"], errors="coerce")
    view = view.sort_values(
        ["_stockout_sort", "库存可售天数", "商品名称"],
        ascending=[True, True, True],
        na_position="last",
    ).drop(columns="_stockout_sort")

    cols = STOCKOUT_FULL_COLS if include_reorder else STOCKOUT_ONLY_COLS
    return view[[c for c in cols if c in view.columns]].reset_index(drop=True)


def stockout_excel_bytes(
    df: pd.DataFrame,
    lang: str,
    history_days: int,
    forecast_days: int,
    sheet_key: str = "stockout_sheet",
) -> bytes:
    from src.i18n import localize_dataframe, t

    display = localize_dataframe(df, lang, history_days, forecast_days)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        display.to_excel(writer, index=False, sheet_name=t(sheet_key, lang))
    return buffer.getvalue()


def save_stockout_excel(
    df: pd.DataFrame,
    lang: str,
    history_days: int,
    forecast_days: int,
    output_dir: str | Path = "output",
) -> Path | None:
    from src.i18n import t

    view = build_stockout_view(df, include_reorder=False)
    if view.empty:
        return None
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_path / t("stockout_filename", lang, ts=timestamp)
    path.write_bytes(
        stockout_excel_bytes(view, lang, history_days, forecast_days),
    )
    return path
