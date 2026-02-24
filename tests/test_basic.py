"""
简单测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加插件路径
sys.path.insert(0, str(Path(__file__).parent))


async def test_imports():
    """测试导入"""
    print("测试导入模块...")
    
    try:
        from core.base import ConfigManager, MEMORY_TYPE_SHORT_TERM, MEMORY_TYPE_LONG_TERM
        print("✓ 基础模块导入成功")
        
        from storage import Database, FaissIndex
        print("✓ 存储模块导入成功")
        
        from retrieval import BM25Retriever, HybridRetriever
        print("✓ 检索模块导入成功")
        
        from summarizer import MemorySummarizer
        print("✓ 总结器模块导入成功")
        
        from managers import MemoryEngine, ConversationManager
        print("✓ 管理器模块导入成功")
        
        from webui import WebUIApp
        print("✓ WebUI 模块导入成功")
        
        print("\n✅ 所有模块导入成功！")
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败：{e}")
        return False


async def test_database():
    """测试数据库"""
    print("\n测试数据库...")
    
    try:
        from storage import Database
        
        db = Database(":memory:")
        print("✓ 数据库创建成功")
        
        # 测试添加短期记忆
        memory_id = await db.add_short_term_memory(
            "test_session",
            "这是一条测试记忆",
            "test_persona"
        )
        print(f"✓ 添加短期记忆成功，ID={memory_id}")
        
        # 测试获取短期记忆
        memories = await db.get_short_term_memories("test_session")
        print(f"✓ 获取短期记忆成功，数量={len(memories)}")
        
        # 测试添加长期记忆
        long_id = await db.add_long_term_memory(
            "test_session",
            "这是一条长期记忆",
            canonical_summary="事实总结",
            persona_summary="人格总结"
        )
        print(f"✓ 添加长期记忆成功，ID={long_id}")
        
        # 测试统计
        stats = await db.get_stats()
        print(f"✓ 获取统计成功：{stats}")
        
        print("\n✅ 数据库测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败：{e}")
        return False


async def test_bm25():
    """测试 BM25 检索"""
    print("\n测试 BM25 检索...")
    
    try:
        from retrieval import BM25Retriever
        
        retriever = BM25Retriever()
        await retriever.initialize()
        
        # 添加文档
        await retriever.add_documents(
            [1, 2, 3],
            ["今天天气很好", "我喜欢吃苹果", "Python 是一门编程语言"]
        )
        print("✓ 添加文档成功")
        
        # 搜索
        results = await retriever.search("天气", k=3)
        print(f"✓ 搜索成功，结果={results}")
        
        # 统计
        count = await retriever.get_document_count()
        print(f"✓ 文档数量={count}")
        
        print("\n✅ BM25 测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ BM25 测试失败：{e}")
        return False


async def main():
    """主测试函数"""
    print("=" * 50)
    print("AstrBot Plugin Unified Memory - 测试脚本")
    print("=" * 50)
    
    results = []
    
    # 运行测试
    results.append(("导入测试", await test_imports()))
    results.append(("数据库测试", await test_database()))
    results.append(("BM25 测试", await test_bm25()))
    
    # 输出结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("=" * 50))
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查错误信息")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())