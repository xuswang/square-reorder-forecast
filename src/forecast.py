"""基于历史销量的进货预测模型。"""

from __future__ import annotations

import math

import pandas as pd


def _fill_daily_series(
    item_df: pd.DataFrame,
    history_days: int,
    end_date: pd.Timestamp | None = None,
) -> pd.Series:
    """将稀疏日销量填充为完整日期序列（无销售日记为 0）。"""
    if end_date is None:
        end_date = pd.Timestamp.today().normalize()
    start_date = end_date - pd.Timedelta(days=history_days - 1)

    full_index = pd.date_range(start=start_date, end=end_date, freq="D")
    if item_df.empty:
        return pd.Series(0.0, index=full_index)

    series = (
        item_df.set_index("date")["quantity"]
        .astype(float)
        .groupby(level=0)
        .sum()
    )
    series.index = pd.to_datetime(series.index)
    return series.reindex(full_index, fill_value=0.0)


def _weighted_daily_rate(daily: pd.Series) -> float:
    """近期加权日均销量：最近 7 天权重 50%，8-30 天 30%，其余 20%。"""
    n = len(daily)
    if n == 0:
        return 0.0

    recent_7 = daily.iloc[-7:].mean() if n >= 1 else 0.0
    mid_23 = daily.iloc[-30:-7].mean() if n > 7 else 0.0
    early = daily.iloc[:-30].mean() if n > 30 else 0.0

    if n <= 7:
        return float(daily.mean())
    if n <= 30:
        return float(recent_7 * 0.6 + daily.iloc[:-7].mean() * 0.4)
    return float(recent_7 * 0.5 + mid_23 * 0.3 + early * 0.2)


def _safety_stock(daily: pd.Series, forecast_days: int, z: float) -> float:
    """基于日销量标准差的安全库存。"""
    if len(daily) < 2:
        return 0.0
    std = float(daily.std(ddof=1))
    return z * std * math.sqrt(forecast_days)


def forecast_reorder(
    sales_daily: pd.DataFrame,
    inventory: pd.DataFrame,
    catalog_names: dict[str, str],
    history_days: int,
    forecast_days: int,
    safety_stock_z: float,
    catalog_for_sale: dict[str, bool] | None = None,
    exclude_not_for_sale: bool = False,
) -> pd.DataFrame:
    """
    预测未来 N 天需求并计算建议进货量。

    建议进货量 = max(0, 预测需求 + 安全库存 - 当前库存)
    """
    if sales_daily.empty and inventory.empty:
        return pd.DataFrame()

    all_ids = set(sales_daily["catalog_object_id"].unique()) | set(
        inventory["catalog_object_id"].unique()
    )

    rows: list[dict] = []
    end_date = pd.Timestamp.today().normalize()

    catalog_for_sale = catalog_for_sale or {}

    for catalog_id in sorted(all_ids):
        for_sale = catalog_for_sale.get(catalog_id, True)
        if exclude_not_for_sale and not for_sale:
            continue

        item_sales = sales_daily[sales_daily["catalog_object_id"] == catalog_id]
        daily = _fill_daily_series(item_sales, history_days, end_date)

        daily_rate = _weighted_daily_rate(daily)
        forecast_qty = daily_rate * forecast_days
        safety = _safety_stock(daily, forecast_days, safety_stock_z)

        stock_row = inventory[inventory["catalog_object_id"] == catalog_id]
        current_stock = (
            float(stock_row["current_stock"].iloc[0]) if not stock_row.empty else 0.0
        )

        reorder_qty = max(0.0, math.ceil(forecast_qty + safety - current_stock))

        total_sold = float(item_sales["quantity"].sum()) if not item_sales.empty else 0.0
        active_days = int((daily > 0).sum())
        name = catalog_names.get(catalog_id)
        if not name and not item_sales.empty:
            name = str(item_sales["item_name"].iloc[-1])
        name = name or catalog_id

        rows.append(
            {
                "商品名称": name,
                "SKU_ID": catalog_id,
                "在售状态": "在售" if for_sale else "停售",
                "当前库存": int(current_stock),
                f"近{history_days}天总销量": int(total_sold),
                "有销售天数": active_days,
                "日均销量(加权)": round(daily_rate, 2),
                f"预测{forecast_days}天需求": round(forecast_qty, 1),
                "安全库存": round(safety, 1),
                "建议进货量": int(reorder_qty),
                "优先级": _priority(reorder_qty, current_stock, daily_rate),
            }
        )

    result = pd.DataFrame(rows)
    if result.empty:
        return result

    return result.sort_values(
        ["建议进货量", "日均销量(加权)"],
        ascending=[False, False],
    ).reset_index(drop=True)


def _priority(reorder_qty: float, current_stock: float, daily_rate: float) -> str:
    if reorder_qty <= 0:
        return "充足"
    if current_stock <= 0:
        return "紧急"
    if daily_rate > 0 and current_stock / daily_rate < 7:
        return "高"
    if daily_rate > 0 and current_stock / daily_rate < 14:
        return "中"
    return "低"
