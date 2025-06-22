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

-- 餐厅基本信息表
CREATE TABLE IF NOT EXISTS restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 餐桌类型表
CREATE TABLE IF NOT EXISTS table_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    capacity INTEGER NOT NULL CHECK(capacity > 0),  -- 桌型容量
    quantity INTEGER NOT NULL CHECK(quantity >= 0), -- 桌型数量
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

-- 时间段库存表（核心）
CREATE TABLE IF NOT EXISTS time_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    table_type_id INTEGER NOT NULL,
    slot_start DATETIME NOT NULL,   -- 时间段开始
    slot_end DATETIME NOT NULL,     -- 时间段结束
    available INTEGER NOT NULL CHECK(available >= 0), -- 可用数量
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    FOREIGN KEY (table_type_id) REFERENCES table_types(id) ON DELETE CASCADE
);

-- 预订记录表（添加了email字段）
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    table_type_id INTEGER NOT NULL,
    customer_name TEXT NOT NULL,
    email TEXT NOT NULL,  -- 新增邮箱字段
    phone TEXT NOT NULL,
    people_count INTEGER NOT NULL,
    slot_start DATETIME NOT NULL,
    slot_end DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
    FOREIGN KEY (table_type_id) REFERENCES table_types(id)
);

-- 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_restaurants_name ON restaurants(name);
CREATE INDEX IF NOT EXISTS idx_table_types_rest ON table_types(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_time_slots_main ON time_slots(restaurant_id, slot_start);
CREATE INDEX IF NOT EXISTS idx_reservations_main ON reservations(restaurant_id, slot_start);
CREATE INDEX IF NOT EXISTS idx_reservations_email ON reservations(email); -- 邮箱索引


---------创建初始化餐厅数据------

-- 步骤1: 插入餐厅基本信息
INSERT OR IGNORE INTO restaurants (name) VALUES 
('广式早茶'),
('川菜馆');

-- 步骤2: 插入桌型配置（使用子查询获取餐厅ID）
INSERT OR IGNORE INTO table_types (restaurant_id, capacity, quantity)
-- 广式早茶桌型
SELECT id, 6, 5 FROM restaurants WHERE name = '广式早茶'
UNION ALL
SELECT id, 5, 4 FROM restaurants WHERE name = '广式早茶'
UNION ALL
SELECT id, 4, 4 FROM restaurants WHERE name = '广式早茶'
UNION ALL
SELECT id, 2, 4 FROM restaurants WHERE name = '广式早茶'
-- 川菜馆桌型
UNION ALL
SELECT id, 6, 5 FROM restaurants WHERE name = '川菜馆'
UNION ALL
SELECT id, 5, 4 FROM restaurants WHERE name = '川菜馆'
UNION ALL
SELECT id, 4, 4 FROM restaurants WHERE name = '川菜馆'
UNION ALL
SELECT id, 2, 4 FROM restaurants WHERE name = '川菜馆';

-- 步骤3: 生成未来7天的时段库存
WITH 
-- 参数配置
config AS (
  SELECT 
    '09:00' AS opening,  -- 开门时间
    '21:00' AS closing,  -- 关门时间
    2 AS duration_hours, -- 每个时段时长(小时)
    7 AS days_ahead      -- 生成未来天数
),
-- 生成日期序列
date_series AS (
  SELECT date('now', '+' || (d.value - 1) || ' days') AS day
  FROM (
    SELECT value FROM generate_series(1, (SELECT days_ahead FROM config))
  AS d
),
-- 生成时段序列
time_slots AS (
  SELECT 
    time(opening, '+' || (t.value - 1) * duration_hours || ' hours') AS slot_time
  FROM (
    SELECT value FROM generate_series(
      0, 
      (CAST(strftime('%H', closing) AS INT) - CAST(strftime('%H', opening) AS INT) / duration_hours - 1
    )
  ) AS t, config
),
-- 组合所有可能的时段
all_slots AS (
  SELECT 
    d.day,
    t.slot_time,
    datetime(d.day || ' ' || t.slot_time) AS slot_start,
    datetime(d.day || ' ' || t.slot_time, '+' || (SELECT duration_hours FROM config) || ' hours') AS slot_end
  FROM date_series d, time_slots t
)
-- 插入库存数据
INSERT OR IGNORE INTO time_slots (restaurant_id, table_type_id, slot_start, slot_end, available)
SELECT 
  tt.restaurant_id,
  tt.id AS table_type_id,
  s.slot_start,
  s.slot_end,
  tt.quantity AS available
FROM table_types tt
CROSS JOIN all_slots s
WHERE tt.restaurant_id IN (SELECT id FROM restaurants);