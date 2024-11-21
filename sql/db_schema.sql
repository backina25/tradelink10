CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    strategy VARCHAR(255),
    order_id VARCHAR(255),
    action VARCHAR(50),
    symbol VARCHAR(50),
    price NUMERIC,
    quantity NUMERIC,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50),
    action VARCHAR(50),
    price NUMERIC,
    quantity NUMERIC,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(50),
    quantity NUMERIC,
    average_price NUMERIC,
    stop_loss NUMERIC,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
