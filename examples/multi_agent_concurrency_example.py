"""
多Agent并发控制示例 - 展示如何避免脏读和脏写
"""
import threading
import time
import random
import subprocess
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# 模拟多个MCP Agent的并发访问
class MockMCPServer:
    """模拟MCP服务器"""
    
    def __init__(self, agent_id: str, db_path: str):
        self.agent_id = agent_id
        self.db_path = db_path
        self.lock_file = f"{db_path}.{agent_id}.lock"
    
    def execute_query(self, query: str, params: tuple = ()) -> list:
        """执行查询（模拟）"""
        # 在实际实现中，这里会调用数据库管理器
        print(f"Agent {self.agent_id}: 执行查询 - {query}")
        time.sleep(random.uniform(0.1, 0.3))
        return [{"id": 1, "name": "测试用户", "version": random.randint(1, 10)}]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新（模拟）"""
        print(f"Agent {self.agent_id}: 执行更新 - {query}")
        time.sleep(random.uniform(0.2, 0.5))
        return 1

def demonstrate_dirty_read_problem():
    """演示脏读问题"""
    print("=== 脏读问题演示 ===")
    
    # 模拟两个Agent同时访问同一数据
    agent1 = MockMCPServer("Agent-1", "data/test.db")
    agent2 = MockMCPServer("Agent-2", "data/test.db")
    
    def agent1_operation():
        """Agent1的操作：读取用户数据"""
        print("Agent1: 开始读取用户数据...")
        result = agent1.execute_query("SELECT * FROM users WHERE id = 1")
        print(f"Agent1: 读取结果 - {result}")
        return result
    
    def agent2_operation():
        """Agent2的操作：修改用户数据"""
        print("Agent2: 开始修改用户数据...")
        time.sleep(0.1)  # 模拟Agent2稍后开始
        result = agent2.execute_update("UPDATE users SET name = '新名字' WHERE id = 1")
        print(f"Agent2: 修改完成，影响行数 - {result}")
        return result
    
    # 并发执行
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(agent1_operation)
        future2 = executor.submit(agent2_operation)
        
        result1 = future1.result()
        result2 = future2.result()
    
    print("问题：Agent1可能读取到Agent2正在修改的数据（脏读）")

def demonstrate_dirty_write_problem():
    """演示脏写问题"""
    print("\n=== 脏写问题演示 ===")
    
    agent1 = MockMCPServer("Agent-1", "data/test.db")
    agent2 = MockMCPServer("Agent-2", "data/test.db")
    
    def agent1_write():
        """Agent1的写操作"""
        print("Agent1: 开始写入数据...")
        time.sleep(0.1)
        result = agent1.execute_update("UPDATE users SET balance = balance + 100 WHERE id = 1")
        print("Agent1: 写入完成")
        return result
    
    def agent2_write():
        """Agent2的写操作"""
        print("Agent2: 开始写入数据...")
        time.sleep(0.1)
        result = agent2.execute_update("UPDATE users SET balance = balance + 200 WHERE id = 1")
        print("Agent2: 写入完成")
        return result
    
    # 并发执行
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(agent1_write)
        future2 = executor.submit(agent2_write)
        
        future1.result()
        future2.result()
    
    print("问题：两个Agent同时修改同一数据，可能导致数据不一致（脏写）")

def demonstrate_solution_with_locks():
    """演示使用锁的解决方案"""
    print("\n=== 使用锁的解决方案 ===")
    
    # 模拟文件锁机制
    lock_file = "data/test.db.lock"
    
    def acquire_lock(agent_id: str, timeout: int = 5) -> bool:
        """获取锁"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with open(lock_file, 'w') as f:
                    f.write(agent_id)
                return True
            except:
                time.sleep(0.1)
        return False
    
    def release_lock():
        """释放锁"""
        try:
            Path(lock_file).unlink(missing_ok=True)
        except:
            pass
    
    def agent1_safe_operation():
        """Agent1的安全操作"""
        print("Agent1: 尝试获取锁...")
        if acquire_lock("Agent-1"):
            try:
                print("Agent1: 获取锁成功，执行操作...")
                time.sleep(1)  # 模拟操作时间
                print("Agent1: 操作完成")
            finally:
                release_lock()
                print("Agent1: 释放锁")
        else:
            print("Agent1: 获取锁失败")
    
    def agent2_safe_operation():
        """Agent2的安全操作"""
        print("Agent2: 尝试获取锁...")
        if acquire_lock("Agent-2"):
            try:
                print("Agent2: 获取锁成功，执行操作...")
                time.sleep(1)  # 模拟操作时间
                print("Agent2: 操作完成")
            finally:
                release_lock()
                print("Agent2: 释放锁")
        else:
            print("Agent2: 获取锁失败")
    
    # 并发执行
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(agent1_safe_operation)
        future2 = executor.submit(agent2_safe_operation)
        
        future1.result()
        future2.result()
    
    print("解决方案：使用文件锁确保同一时间只有一个Agent可以修改数据")

def demonstrate_optimistic_locking():
    """演示乐观锁解决方案"""
    print("\n=== 乐观锁解决方案 ===")
    
    class OptimisticLockManager:
        def __init__(self):
            self.data = {"id": 1, "name": "用户", "version": 1}
            self.lock = threading.Lock()
        
        def read_data(self, agent_id: str):
            """读取数据"""
            with self.lock:
                print(f"{agent_id}: 读取数据 - {self.data}")
                return self.data.copy()
        
        def update_data(self, agent_id: str, new_name: str, expected_version: int):
            """更新数据（乐观锁）"""
            with self.lock:
                if self.data["version"] != expected_version:
                    print(f"{agent_id}: 版本冲突！期望版本 {expected_version}，实际版本 {self.data['version']}")
                    return False
                
                self.data["name"] = new_name
                self.data["version"] += 1
                print(f"{agent_id}: 更新成功 - {self.data}")
                return True
    
    manager = OptimisticLockManager()
    
    def agent1_optimistic_operation():
        """Agent1的乐观锁操作"""
        print("Agent1: 开始乐观锁操作...")
        # 读取数据
        data = manager.read_data("Agent1")
        time.sleep(0.5)  # 模拟处理时间
        
        # 尝试更新
        success = manager.update_data("Agent1", "Agent1修改的名字", data["version"])
        if success:
            print("Agent1: 更新成功")
        else:
            print("Agent1: 更新失败，需要重试")
    
    def agent2_optimistic_operation():
        """Agent2的乐观锁操作"""
        print("Agent2: 开始乐观锁操作...")
        # 读取数据
        data = manager.read_data("Agent2")
        time.sleep(0.3)  # 模拟处理时间
        
        # 尝试更新
        success = manager.update_data("Agent2", "Agent2修改的名字", data["version"])
        if success:
            print("Agent2: 更新成功")
        else:
            print("Agent2: 更新失败，需要重试")
    
    # 并发执行
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(agent1_optimistic_operation)
        future2 = executor.submit(agent2_optimistic_operation)
        
        future1.result()
        future2.result()
    
    print("解决方案：使用乐观锁，只有在版本匹配时才允许更新")

def demonstrate_transaction_isolation():
    """演示事务隔离级别"""
    print("\n=== 事务隔离级别演示 ===")
    
    isolation_levels = {
        "read_uncommitted": "读未提交 - 可能发生脏读",
        "read_committed": "读已提交 - 避免脏读",
        "serializable": "串行化 - 最高隔离级别"
    }
    
    for level, description in isolation_levels.items():
        print(f"\n{level}: {description}")
        
        def simulate_transaction(agent_id: str, isolation: str):
            print(f"{agent_id}: 开始事务 ({isolation})...")
            if isolation == "serializable":
                print(f"{agent_id}: 获取排他锁")
                time.sleep(0.5)
                print(f"{agent_id}: 执行操作")
                time.sleep(0.3)
                print(f"{agent_id}: 提交事务，释放锁")
            else:
                print(f"{agent_id}: 执行操作")
                time.sleep(0.3)
                print(f"{agent_id}: 提交事务")
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(simulate_transaction, "Agent1", level)
            future2 = executor.submit(simulate_transaction, "Agent2", level)
            
            future1.result()
            future2.result()

def main():
    """主函数"""
    print("多Agent并发控制演示")
    print("=" * 50)
    
    # 清理之前的锁文件
    Path("data/test.db.lock").unlink(missing_ok=True)
    
    try:
        # 1. 演示问题
        demonstrate_dirty_read_problem()
        demonstrate_dirty_write_problem()
        
        # 2. 演示解决方案
        demonstrate_solution_with_locks()
        demonstrate_optimistic_locking()
        demonstrate_transaction_isolation()
        
        print("\n" + "=" * 50)
        print("演示完成！")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
    finally:
        # 清理锁文件
        Path("data/test.db.lock").unlink(missing_ok=True)

if __name__ == "__main__":
    main() 