"""从 Square API 拉取订单、库存和商品目录数据。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
from square import Square
from square.core.api_error import ApiError
from square.environment import SquareEnvironment

from config import Settings


@dataclass(frozen=True)
class CatalogMeta:
    name: str
    for_sale: bool


def _check_errors(response: Any, context: str) -> None:
    errors = getattr(response, "errors", None)
    if errors:
        msgs = "; ".join(f"{e.category}: {e.code} - {e.detail}" for e in errors)
        raise RuntimeError(f"{context} 失败: {msgs}")


def create_client(settings: Settings) -> Square:
    env = (
        SquareEnvironment.SANDBOX
        if settings.environment == "sandbox"
        else SquareEnvironment.PRODUCTION
    )
    return Square(token=settings.access_token, environment=env)


def get_location_id(client: Square, settings: Settings) -> str:
    if settings.location_id:
        return settings.location_id

    response = client.locations.list()
    _check_errors(response, "获取门店列表")
    locations = response.locations or []
    active = [loc for loc in locations if getattr(loc, "status", None) == "ACTIVE"]
    if not active:
        active = locations
    if not active:
        raise RuntimeError("未找到任何 Square 门店，请检查 API Token 权限。")
    return active[0].id


def fetch_sales_history(
    client: Square,
    location_id: str,
    history_days: int,
) -> pd.DataFrame:
    """拉取历史订单，返回每日 SKU 销量 DataFrame。"""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=history_days)
    start_rfc = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_rfc = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    query = {
        "filter": {
            "state_filter": {"states": ["COMPLETED"]},
            "date_time_filter": {
                "closed_at": {"start_at": start_rfc, "end_at": end_rfc},
            },
        },
        "sort": {"sort_field": "CLOSED_AT", "sort_order": "ASC"},
    }

    records: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        try:
            response = client.orders.search(
                location_ids=[location_id],
                query=query,
                limit=500,
                cursor=cursor,
                return_entries=False,
            )
        except ApiError as exc:
            raise RuntimeError(f"搜索订单失败: {exc}") from exc

        _check_errors(response, "搜索订单")

        for order in response.orders or []:
            closed_at = order.closed_at or order.created_at
            if not closed_at:
                continue
            sale_date = pd.to_datetime(closed_at).date()

            for item in order.line_items or []:
                catalog_id = item.catalog_object_id
                if not catalog_id:
                    continue
                try:
                    qty = float(item.quantity)
                except (TypeError, ValueError):
                    continue
                if qty <= 0:
                    continue

                records.append(
                    {
                        "date": sale_date,
                        "catalog_object_id": catalog_id,
                        "item_name": item.name or catalog_id,
                        "quantity": qty,
                    }
                )

        cursor = response.cursor
        if not cursor:
            break

    if not records:
        return pd.DataFrame(
            columns=["date", "catalog_object_id", "item_name", "quantity"]
        )

    df = pd.DataFrame(records)
    daily = (
        df.groupby(["date", "catalog_object_id", "item_name"], as_index=False)["quantity"]
        .sum()
        .sort_values(["catalog_object_id", "date"])
    )
    return daily


def fetch_inventory(client: Square, location_id: str) -> pd.DataFrame:
    """拉取当前在库库存。"""
    records: list[dict[str, Any]] = []

    try:
        pager = client.inventory.batch_get_counts(
            location_ids=[location_id],
            states=["IN_STOCK"],
            limit=100,
        )
    except ApiError as exc:
        raise RuntimeError(f"获取库存失败: {exc}") from exc

    for count in pager:
        qty = count.quantity
        if qty is None:
            continue
        try:
            qty_val = float(qty)
        except (TypeError, ValueError):
            continue

        records.append(
            {
                "catalog_object_id": count.catalog_object_id,
                "current_stock": qty_val,
                "calculated_at": count.calculated_at,
            }
        )

    if not records:
        return pd.DataFrame(columns=["catalog_object_id", "current_stock", "calculated_at"])

    df = pd.DataFrame(records)
    return (
        df.sort_values("calculated_at", ascending=False)
        .drop_duplicates(subset=["catalog_object_id"], keep="first")
        .reset_index(drop=True)
    )


def fetch_catalog_metadata(
    client: Square,
    catalog_ids: list[str],
    location_id: str | None = None,
) -> dict[str, CatalogMeta]:
    """批量获取商品名称及在售状态（variation ID -> CatalogMeta）。"""
    if not catalog_ids:
        return {}

    meta: dict[str, CatalogMeta] = {}
    item_names: dict[str, str] = {}
    items_by_id: dict[str, Any] = {}
    batch_size = 100

    for i in range(0, len(catalog_ids), batch_size):
        batch = catalog_ids[i : i + batch_size]
        try:
            response = client.catalog.batch_get(
                object_ids=batch,
                include_related_objects=True,
            )
        except ApiError as exc:
            raise RuntimeError(f"获取商品目录失败: {exc}") from exc

        _check_errors(response, "获取商品目录")

        for obj in response.related_objects or []:
            if obj.type == "ITEM" and obj.item_data and obj.item_data.name:
                item_names[obj.id] = obj.item_data.name
                items_by_id[obj.id] = obj

        for obj in response.objects or []:
            if obj.type == "ITEM" and obj.item_data and obj.item_data.name:
                item_names[obj.id] = obj.item_data.name
                items_by_id[obj.id] = obj
                if obj.item_data.variations:
                    for var in obj.item_data.variations:
                        if not var.id:
                            continue
                        parent_name = obj.item_data.name
                        meta[var.id] = CatalogMeta(
                            name=_variation_display_name(parent_name, var),
                            for_sale=_is_for_sale(var, obj, location_id),
                        )

            elif obj.type == "ITEM_VARIATION" and obj.item_variation_data:
                parent_id = obj.item_variation_data.item_id
                parent = items_by_id.get(parent_id) if parent_id else None
                parent_name = item_names.get(parent_id, "") if parent_id else ""
                meta[obj.id] = CatalogMeta(
                    name=_variation_display_name(parent_name, obj),
                    for_sale=_is_for_sale(obj, parent, location_id),
                )

    return meta


def fetch_catalog_names(client: Square, catalog_ids: list[str]) -> dict[str, str]:
    """兼容接口：仅返回商品名称。"""
    metadata = fetch_catalog_metadata(client, catalog_ids)
    return {cid: m.name for cid, m in metadata.items()}


def _present_at_location(obj: Any, location_id: str | None) -> bool:
    if not location_id:
        return True
    if getattr(obj, "is_deleted", None):
        return False
    absent = getattr(obj, "absent_at_location_ids", None) or []
    if location_id in absent:
        return False
    if getattr(obj, "present_at_all_locations", None) is False:
        present = getattr(obj, "present_at_location_ids", None) or []
        return location_id in present
    return True


def _is_for_sale(variation: Any, parent_item: Any | None, location_id: str | None) -> bool:
    if getattr(variation, "is_deleted", None):
        return False
    if parent_item and getattr(parent_item, "is_deleted", None):
        return False
    if parent_item and parent_item.item_data and parent_item.item_data.is_archived:
        return False
    if not _present_at_location(variation, location_id):
        return False
    if parent_item and not _present_at_location(parent_item, location_id):
        return False

    vd = variation.item_variation_data
    if not vd:
        return True
    if vd.sellable is False:
        return False

    if location_id and vd.location_overrides:
        for override in vd.location_overrides:
            if override.location_id == location_id and override.sold_out:
                return False

    return True


def _variation_display_name(parent_name: str, var_obj: Any) -> str:
    var_name = ""
    if var_obj.item_variation_data and var_obj.item_variation_data.name:
        var_name = var_obj.item_variation_data.name
    if parent_name and var_name and var_name.lower() != "regular":
        return f"{parent_name} ({var_name})"
    if parent_name:
        return parent_name
    return var_name or var_obj.id
