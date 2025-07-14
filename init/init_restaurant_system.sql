-- 餐厅预订系统初始化脚本
-- 包含完整的表结构、索引和基础数据

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    age INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 餐厅基本信息表
CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address TEXT,
    phone TEXT,
    business_hours TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 餐桌类型表
CREATE TABLE IF NOT EXISTS table_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    capacity INTEGER NOT NULL CHECK(capacity > 0),
    quantity INTEGER NOT NULL CHECK(quantity >= 0),
    description TEXT,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

-- 时间段库存表
CREATE TABLE IF NOT EXISTS time_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    table_type_id INTEGER NOT NULL,
    slot_start DATETIME NOT NULL,
    slot_end DATETIME NOT NULL,
    available INTEGER NOT NULL CHECK(available >= 0),
    total INTEGER NOT NULL CHECK(total >= 0),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    FOREIGN KEY (table_type_id) REFERENCES table_types(id) ON DELETE CASCADE
);

-- 预订记录表
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

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_restaurants_name ON restaurants(name);
CREATE INDEX IF NOT EXISTS idx_table_types_rest ON table_types(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_time_slots_main ON time_slots(restaurant_id, slot_start);
CREATE INDEX IF NOT EXISTS idx_reservations_main ON reservations(restaurant_id, slot_start);
CREATE INDEX IF NOT EXISTS idx_reservations_email ON reservations(email);

-- 插入基础餐厅数据
INSERT OR IGNORE INTO restaurants (name, address, phone, business_hours) VALUES
    ('广式早茶', '天河路100号', '020-12345678', '07:00-14:00'),
    ('川菜馆', '人民中路200号', '020-87654321', '10:00-22:00'),
    ('日料店', '珠江新城300号', '020-11111111', '11:00-21:00'),
    ('西餐厅', '越秀区400号', '020-22222222', '11:00-23:00');

-- 插入桌型数据
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 6, 5, '6人桌' FROM restaurants WHERE name = '广式早茶';

INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 5, 4, '5人桌' FROM restaurants WHERE name = '广式早茶';

INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 4, 4, '4人桌' FROM restaurants WHERE name = '广式早茶';

INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 2, 4, '2人桌' FROM restaurants WHERE name = '广式早茶';

-- 川菜馆桌型
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 6, 5, '6人桌' FROM restaurants WHERE name = '川菜馆';

INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 5, 4, '5人桌' FROM restaurants WHERE name = '川菜馆';

INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 4, 4, '4人桌' FROM restaurants WHERE name = '川菜馆';

INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 2, 4, '2人桌' FROM restaurants WHERE name = '川菜馆';

-- 日料店桌型
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 6, 3, '6人桌' FROM restaurants WHERE name = '日料店';

INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 4, 4, '4人桌' FROM restaurants WHERE name = '日料店';

INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 2, 6, '2人桌' FROM restaurants WHERE name = '日料店';

-- 西餐厅桌型
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 8, 2, '8人桌' FROM restaurants WHERE name = '西餐厅';

INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 6, 3, '6人桌' FROM restaurants WHERE name = '西餐厅';

INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 4, 4, '4人桌' FROM restaurants WHERE name = '西餐厅';

INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity, description)
SELECT id, 2, 4, '2人桌' FROM restaurants WHERE name = '西餐厅';
