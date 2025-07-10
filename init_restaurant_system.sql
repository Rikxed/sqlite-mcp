-- 餐厅预订系统初始化脚本
-- 适用于标准MCP版本，手动执行此脚本创建完整的预订系统

-- 1. 创建餐厅基本信息表
CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address TEXT,
    phone TEXT,
    business_hours TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. 创建餐桌类型表
CREATE TABLE IF NOT EXISTS table_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    capacity INTEGER NOT NULL CHECK(capacity > 0),
    quantity INTEGER NOT NULL CHECK(quantity >= 0),
    description TEXT,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

-- 3. 创建预订记录表
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    table_type_id INTEGER NOT NULL,
    customer_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    people_count INTEGER NOT NULL,
    slot_start DATETIME NOT NULL,
    slot_end DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
    FOREIGN KEY (table_type_id) REFERENCES table_types(id)
);

-- 4. 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_restaurants_name ON restaurants(name);
CREATE INDEX IF NOT EXISTS idx_table_types_rest ON table_types(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_reservations_main ON reservations(restaurant_id, slot_start);
CREATE INDEX IF NOT EXISTS idx_reservations_email ON reservations(email);

-- 5. 插入示例餐厅数据
INSERT OR IGNORE INTO restaurants (name, address, phone, business_hours) VALUES
    ('广式早茶', '天河路100号', '020-12345678', '07:00-14:00'),
    ('川菜馆', '人民中路200号', '020-87654321', '10:00-22:00'),
    ('日料店', '珠江新城300号', '020-11223344', '11:00-21:00'),
    ('西餐厅', '太古汇400号', '020-55667788', '11:00-23:00');

-- 6. 插入桌型数据
-- 广式早茶桌型
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 6, 5, '6人桌' FROM restaurants WHERE name = '广式早茶';
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 4, 8, '4人桌' FROM restaurants WHERE name = '广式早茶';
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 2, 10, '2人桌' FROM restaurants WHERE name = '广式早茶';

-- 川菜馆桌型
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 8, 3, '8人桌' FROM restaurants WHERE name = '川菜馆';
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 6, 6, '6人桌' FROM restaurants WHERE name = '川菜馆';
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 4, 8, '4人桌' FROM restaurants WHERE name = '川菜馆';
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 2, 12, '2人桌' FROM restaurants WHERE name = '川菜馆';

-- 日料店桌型
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 6, 4, '6人桌' FROM restaurants WHERE name = '日料店';
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 4, 6, '4人桌' FROM restaurants WHERE name = '日料店';
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 2, 8, '2人桌' FROM restaurants WHERE name = '日料店';

-- 西餐厅桌型
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 8, 2, '8人桌' FROM restaurants WHERE name = '西餐厅';
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 6, 4, '6人桌' FROM restaurants WHERE name = '西餐厅';
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 4, 6, '4人桌' FROM restaurants WHERE name = '西餐厅';
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 2, 10, '2人桌' FROM restaurants WHERE name = '西餐厅';

-- 7. 验证数据
SELECT '餐厅数据' as table_name, COUNT(*) as count FROM restaurants
UNION ALL
SELECT '桌型数据', COUNT(*) FROM table_types
UNION ALL
SELECT '预订记录', COUNT(*) FROM reservations; 