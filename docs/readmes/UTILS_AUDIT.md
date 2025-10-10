# Utils Audit (2025-09-24T21:24:57.324437Z)

| module | usage | overlap | public_funcs | public_classes | stubs | loc | comments | recommendation |
|---|---:|:---:|---|---|---|---:|---:|---|
|__init__|0|False||||0|0|REVIEW (unused)|
|auto_exit_policy|0|False|resolve_sl_tp,should_send_auto_exits|||41|3|REVIEW (unused)|
|balance_provider|0|False|wallet_usdt|||74|6|REVIEW (unused)|
|exit_adapter|2|False|preview_exits,send_exits|||85|4|KEEP|
|live_bridge|1|False|set_leverage,place_order_fixed|||81|5|KEEP|
|logrotate|0|False|rotate_logs|||82|5|REVIEW (unused)|
|order_adapter|3|False|build_order|||108|2|KEEP|
|order_service|2|False|place|RiskStatePersist||115|9|KEEP|
|position_sizer|5|False|public_price,public_filters,compute_qty_leverage|SizerConfig,SizerResult||54|1|KEEP|
|risk_guard|4|True|can_trade|RiskLimits,RiskState||25|1|MOVE (merge with existing module)|
|sender_adapter|6|False|set_leverage_via_rest,place_order_via_rest|||149|10|KEEP|
|signer|1|False|timestamp_ms,sign_query|||14|1|KEEP|

> overlap = модуль з такою ж назвою вже існує у `core/` або `app/`.
