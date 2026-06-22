"""预测流程（CLI 与 GUI 共用）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from config import Settings
from src.forecast import forecast_reorder
from src.square_client import (
    create_client,
    fetch_catalog_metadata,
    fetch_inventory,
    fetch_sales_history,
    get_location_id,
)

ProgressCallback = Callable[[str, float | None], None]


@dataclass
class ForecastResult:
    df: pd.DataFrame
    location_id: str
    history_days: int
    forecast_days: int
    sales_records: int
    product_count: int
    inventory_count: int
    excluded_not_for_sale: int = 0


def _noop_progress(message: str, fraction: float | None = None) -> None:
    pass


def run_forecast(
    settings: Settings,
    history_days: int | None = None,
    forecast_days: int | None = None,
    safety_stock_z: float | None = None,
    on_progress: ProgressCallback = _noop_progress,
    lang: str = "en",
    exclude_not_for_sale: bool = False,
) -> ForecastResult:
    from src.i18n import t

    history_days = history_days or settings.history_days
    forecast_days = forecast_days or settings.forecast_days
    safety_stock_z = safety_stock_z if safety_stock_z is not None else settings.safety_stock_z

    on_progress(t("prog_connecting", lang), 0.05)
    client = create_client(settings)
    location_id = get_location_id(client, settings)
    on_progress(t("prog_connected", lang, loc=location_id), 0.1)

    on_progress(t("prog_fetch_orders", lang, days=history_days), 0.15)
    sales = fetch_sales_history(client, location_id, history_days)
    product_count = int(sales["catalog_object_id"].nunique()) if not sales.empty else 0
    on_progress(
        t("prog_orders_done", lang, records=len(sales), products=product_count),
        0.45,
    )

    on_progress(t("prog_fetch_inventory", lang), 0.5)
    inventory = fetch_inventory(client, location_id)
    on_progress(t("prog_inventory_done", lang, count=len(inventory)), 0.65)

    catalog_ids = list(
        set(sales["catalog_object_id"].unique().tolist())
        | set(inventory["catalog_object_id"].unique().tolist())
    )
    on_progress(t("prog_fetch_names", lang, count=len(catalog_ids)), 0.7)
    catalog_meta = fetch_catalog_metadata(client, catalog_ids, location_id)
    catalog_names = {cid: m.name for cid, m in catalog_meta.items()}
    catalog_for_sale = {cid: m.for_sale for cid, m in catalog_meta.items()}
    catalog_skus = {cid: m.sku for cid, m in catalog_meta.items()}
    all_product_ids = set(catalog_ids)
    excluded_count = (
        sum(1 for cid in all_product_ids if not catalog_for_sale.get(cid, True))
        if exclude_not_for_sale
        else 0
    )
    on_progress(t("prog_names_done", lang), 0.85)

    on_progress(t("prog_running_model", lang), 0.9)
    result = forecast_reorder(
        sales_daily=sales,
        inventory=inventory,
        catalog_names=catalog_names,
        history_days=history_days,
        forecast_days=forecast_days,
        safety_stock_z=safety_stock_z,
        catalog_for_sale=catalog_for_sale,
        catalog_skus=catalog_skus,
        exclude_not_for_sale=exclude_not_for_sale,
    )
    on_progress(t("prog_complete", lang), 1.0)

    return ForecastResult(
        df=result,
        location_id=location_id,
        history_days=history_days,
        forecast_days=forecast_days,
        sales_records=len(sales),
        product_count=product_count,
        inventory_count=len(inventory),
        excluded_not_for_sale=excluded_count,
    )
