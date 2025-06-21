"""
并发使用示例 - 展示线程安全的数据库操作
"""
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from database.connection import thread_safe_db_manager

def concurrent_read_operations():
    """并发读操作示例"""
    print("=== 并发读操作测试 ===")
    
    def read_user_data(user_id):
        """读取用户数据"""
        try:
            query = "SELECT * FROM users WHERE id = ?"
            result = thread_safe_db_manager.execute_query(query, (user_id,))
            print(f"线程 {threading.current_thread().name}: 读取用户 {user_id} 数据: {result}")
            return result
        except Exception as e:
            print(f"线程 {threading.current_thread().name}: 读取失败 - {e}")
            return None
    
    # 创建多个线程同时读取数据
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(read_user_data, i) for i in range(1, 6)]
        for future in as_completed(futures):
            future.result()

def concurrent_write_operations():
    """并发写操作示例"""
    print("\n=== 并发写操作测试 ===")
    
    def write_user_data(user_data):
        """写入用户数据"""
        try:
            name, email, age = user_data
            query = "INSERT INTO users (name, email, age) VALUES (?, ?, ?)"
            affected_rows = thread_safe_db_manager.execute_update(query, (name, email, age))
            print(f"线程 {threading.current_thread().name}: 插入用户 {name}, 影响行数: {affected_rows}")
            return affected_rows
        except Exception as e:
            print(f"线程 {threading.current_thread().name}: 写入失败 - {e}")
            return 0
    
    # 准备测试数据
    test_users = [
        ("并发用户1", "concurrent1@example.com", 25),
        ("并发用户2", "concurrent2@example.com", 30),
        ("并发用户3", "concurrent3@example.com", 28),
        ("并发用户4", "concurrent4@example.com", 35),
        ("并发用户5", "concurrent5@example.com", 27),
    ]
    
    # 创建多个线程同时写入数据
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(write_user_data, user_data) for user_data in test_users]
        for future in as_completed(futures):
            future.result()

def concurrent_read_write_operations():
    """并发读写操作示例"""
    print("\n=== 并发读写操作测试 ===")
    
    def read_operation():
        """读操作"""
        for _ in range(3):
            try:
                query = "SELECT COUNT(*) as count FROM users"
                result = thread_safe_db_manager.execute_query(query)
                print(f"线程 {threading.current_thread().name}: 用户总数: {result[0]['count']}")
                time.sleep(random.uniform(0.1, 0.3))
            except Exception as e:
                print(f"线程 {threading.current_thread().name}: 读取失败 - {e}")
    
    def write_operation():
        """写操作"""
        for i in range(3):
            try:
                name = f"读写测试用户{i+1}"
                email = f"rwtest{i+1}@example.com"
                age = random.randint(20, 40)
                query = "INSERT INTO users (name, email, age) VALUES (?, ?, ?)"
                affected_rows = thread_safe_db_manager.execute_update(query, (name, email, age))
                print(f"线程 {threading.current_thread().name}: 插入用户 {name}, 影响行数: {affected_rows}")
                time.sleep(random.uniform(0.2, 0.4))
            except Exception as e:
                print(f"线程 {threading.current_thread().name}: 写入失败 - {e}")
    
    # 创建读线程和写线程
    read_threads = [threading.Thread(target=read_operation, name=f"Reader-{i}") for i in range(3)]
    write_threads = [threading.Thread(target=write_operation, name=f"Writer-{i}") for i in range(2)]
    
    # 启动所有线程
    for thread in read_threads + write_threads:
        thread.start()
    
    # 等待所有线程完成
    for thread in read_threads + write_threads:
        thread.join()

def transaction_example():
    """事务操作示例"""
    print("\n=== 事务操作测试 ===")
    
    def complex_transaction():
        """复杂事务操作"""
        try:
            # 定义事务操作
            operations = [
                ("INSERT INTO users (name, email, age) VALUES (?, ?, ?)", ("事务用户1", "tx1@example.com", 25)),
                ("INSERT INTO products (name, price, category) VALUES (?, ?, ?)", ("事务产品1", 100.0, "测试")),
                ("INSERT INTO orders (user_id, product_id, quantity, total_price) VALUES (?, ?, ?, ?)", (1, 1, 2, 200.0))
            ]
            
            success = thread_safe_db_manager.execute_transaction(operations)
            print(f"线程 {threading.current_thread().name}: 事务执行{'成功' if success else '失败'}")
            return success
        except Exception as e:
            print(f"线程 {threading.current_thread().name}: 事务失败 - {e}")
            return False
    
    # 并发执行事务
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(complex_transaction) for _ in range(3)]
        for future in as_completed(futures):
            future.result()

def performance_test():
    """性能测试"""
    print("\n=== 性能测试 ===")
    
    def benchmark_operation(operation_type, iterations=100):
        """性能基准测试"""
        start_time = time.time()
        
        if operation_type == "read":
            for _ in range(iterations):
                thread_safe_db_manager.execute_query("SELECT COUNT(*) FROM users")
        elif operation_type == "write":
            for i in range(iterations):
                thread_safe_db_manager.execute_update(
                    "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
                    (f"性能测试用户{i}", f"perf{i}@example.com", 25)
                )
        
        end_time = time.time()
        duration = end_time - start_time
        ops_per_second = iterations / duration
        
        print(f"{operation_type}操作: {iterations}次, 耗时: {duration:.2f}秒, 每秒操作数: {ops_per_second:.2f}")
        return ops_per_second
    
    # 测试读操作性能
    read_performance = benchmark_operation("read", 100)
    
    # 测试写操作性能
    write_performance = benchmark_operation("write", 50)
    
    print(f"\n性能总结:")
    print(f"读操作: {read_performance:.2f} ops/sec")
    print(f"写操作: {write_performance:.2f} ops/sec")

def main():
    """主函数"""
    print("开始并发数据库操作测试...")
    
    try:
        # 1. 并发读操作测试
        concurrent_read_operations()
        
        # 2. 并发写操作测试
        concurrent_write_operations()
        
        # 3. 并发读写操作测试
        concurrent_read_write_operations()
        
        # 4. 事务操作测试
        transaction_example()
        
        # 5. 性能测试
        performance_test()
        
        print("\n所有测试完成！")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    finally:
        # 清理资源
        thread_safe_db_manager.close()

if __name__ == "__main__":
    main() 