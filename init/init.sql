-- SQLite MCP服务器初始化脚本
-- 这个脚本会在服务器启动时自动执行

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建产品表
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建订单表
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    product_id INTEGER,
    quantity INTEGER NOT NULL,
    total_price REAL NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- 插入示例数据
INSERT OR IGNORE INTO users (id, name, email, age) VALUES 
(1, '张三', 'zhangsan@example.com', 25),
(2, '李四', 'lisi@example.com', 30),
(3, '王五', 'wangwu@example.com', 28);

INSERT OR IGNORE INTO products (id, name, price, category) VALUES 
(1, '笔记本电脑', 5999.00, '电子产品'),
(2, '手机', 2999.00, '电子产品'),
(3, '书籍', 59.00, '图书');

INSERT OR IGNORE INTO orders (id, user_id, product_id, quantity, total_price) VALUES 
(1, 1, 1, 1, 5999.00),
(2, 2, 2, 2, 5998.00),
(3, 3, 3, 5, 295.00); 