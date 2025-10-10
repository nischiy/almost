# core/utils/filters_patch.py
# Optional utility to patch a filters object explicitly from your code if ever needed.
def ensure_filters_get(filters_obj):
    cls = getattr(filters_obj, "__class__", None)
    if not isinstance(cls, type):
        return filters_obj
    if hasattr(cls, "get"):
        return filters_obj
    def _get(self, key, default=None):
        k = str(key)
        if hasattr(self, k):
            return getattr(self, k)
        aliases = {
            "tick_size": ("tick_size", "tickSize", "price_tick_size", "priceTickSize"),
            "step_size": ("step_size", "stepSize", "qty_step_size", "quantity_step_size"),
            "min_notional": ("min_notional", "minNotional", "minNotionalValue", "notional_min"),
            "min_qty": ("min_qty", "minQty", "minQuantity", "quantity_min"),
            "max_qty": ("max_qty", "maxQty", "maxQuantity", "quantity_max"),
            "min_price": ("min_price", "minPrice"),
            "max_price": ("max_price", "maxPrice"),
        }
        if k in aliases:
            for alias in aliases[k]:
                if hasattr(self, alias):
                    return getattr(self, alias)
        d = getattr(self, "__dict__", {}) or {}
        if k in d:
            return d[k]
        lower = {str(kk).lower(): vv for kk, vv in d.items()}
        return lower.get(k.lower(), default)
    try:
        setattr(cls, "get", _get)
    except Exception:
        pass
    return filters_obj
