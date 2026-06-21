-- Initial database schema for KATS persistence

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL,
    order_branch TEXT NOT NULL DEFAULT '',
    symbol_code TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity TEXT NOT NULL,
    price TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'submitted',
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);

CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_no TEXT NOT NULL,
    symbol_code TEXT NOT NULL,
    stock_name TEXT NOT NULL DEFAULT '',
    quantity TEXT NOT NULL,
    average_price TEXT NOT NULL,
    current_price TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_positions_account_symbol
    ON positions(account_no, symbol_code);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_no TEXT NOT NULL,
    total_asset TEXT NOT NULL,
    total_evaluation TEXT NOT NULL,
    total_profit_loss TEXT NOT NULL,
    profit_rate TEXT NOT NULL,
    cash_total TEXT NOT NULL,
    cash_orderable TEXT NOT NULL,
    position_count INTEGER NOT NULL DEFAULT 0,
    snapshot_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS strategies (
    strategy_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    strategy_type TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    parameters_json TEXT NOT NULL DEFAULT '{}',
    symbols_json TEXT NOT NULL DEFAULT '[]',
    state TEXT NOT NULL DEFAULT 'created',
    statistics_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_name TEXT NOT NULL UNIQUE,
    max_order_amount TEXT NOT NULL,
    max_order_quantity TEXT NOT NULL,
    max_position_count INTEGER NOT NULL,
    max_symbol_weight TEXT NOT NULL,
    daily_loss_limit TEXT NOT NULL,
    duplicate_order_block INTEGER NOT NULL DEFAULT 1,
    emergency_stop INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_type TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    symbols_json TEXT NOT NULL DEFAULT '[]',
    initial_capital TEXT NOT NULL,
    final_asset TEXT NOT NULL,
    total_return_rate TEXT NOT NULL,
    win_rate TEXT NOT NULL,
    profit_loss_ratio TEXT NOT NULL,
    profit_factor TEXT NOT NULL,
    max_drawdown TEXT NOT NULL,
    trade_count INTEGER NOT NULL DEFAULT 0,
    average_profit TEXT NOT NULL,
    average_loss TEXT NOT NULL,
    equity_curve_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'INFO',
    source_event TEXT NOT NULL DEFAULT '',
    context_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS system_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
