#!/usr/bin/env python3
"""
快速场景验证 - 在当前环境中测试关键机制

验证三个关键点：
1. 路由系统错误提示质量
2. 已安装包的功能正常性
3. 包依赖关系的正确性
"""

import sys
import tempfile
import json
import subprocess
from pathlib import Path


def test_scenario_1_error_messages():
    """场景1: 测试错误消息质量"""
    print("🧪 场景1: 错误消息质量测试")
    print("-" * 50)
    
    try:
        import opendal
        
        # 测试路由到不同包的服务
        test_services = [
            ('redis', 'database'),
            ('sqlite', 'database'),
            ('dropbox', 'cloud'),
            ('azfile', 'advanced')
        ]
        
        results = {}
        
        for service, expected_package in test_services:
            print(f"\n测试 {service} (期望路由到 {expected_package}):")
            
            try:
                # 检查路由是否正确
                actual_package = opendal._get_service_package(service)
                print(f"  路由: {service} -> {actual_package}")
                
                # 尝试创建 Operator
                if service == 'redis':
                    config = {'endpoint': 'redis://localhost:6379'}
                elif service == 'sqlite':
                    config = {'connection_string': 'sqlite:///test.db', 'table': 'test'}
                elif service == 'dropbox':
                    config = {'access_token': 'test_token'}
                elif service == 'azfile':
                    config = {'endpoint': 'https://test.file.core.windows.net', 'share_name': 'test'}
                else:
                    config = {}
                
                op = opendal.Operator(service, **config)
                print(f"  ✅ {service}: Operator 创建成功")
                results[service] = "success"
                
            except ImportError as e:
                error_msg = str(e)
                print(f"  ❌ {service}: ImportError - {error_msg}")
                
                # 检查错误消息是否有用
                if "install" in error_msg.lower() or expected_package in error_msg.lower():
                    print(f"  ✅ 错误消息有用")
                    results[service] = "useful_error"
                else:
                    print(f"  ⚠️ 错误消息不够有用")
                    results[service] = "unclear_error"
                    
            except Exception as e:
                print(f"  ⚠️ {service}: 其他错误 - {type(e).__name__}: {e}")
                results[service] = "other_error"
        
        return results
        
    except ImportError as e:
        print(f"❌ 无法导入 opendal: {e}")
        return {"import_error": str(e)}


def test_scenario_2_installed_functionality():
    """场景2: 测试已安装包的功能"""
    print("\n🧪 场景2: 已安装包功能测试")
    print("-" * 50)
    
    try:
        import opendal
        
        # 测试可以完整测试的服务
        testable_services = [
            ('memory', {}),
            ('fs', {'root': tempfile.gettempdir()}),
            ('dashmap', {}),
            ('moka', {}),
        ]
        
        results = {}
        
        for service, config in testable_services:
            print(f"\n测试 {service}:")
            
            try:
                op = opendal.Operator(service, **config)
                print(f"  ✅ Operator 创建成功")
                
                # I/O 测试
                test_key = f"test_{service}"
                test_data = b"Quick test data"
                
                op.write(test_key, test_data)
                read_data = op.read(test_key)
                
                if read_data == test_data:
                    print(f"  ✅ I/O 测试成功")
                    
                    # 元数据测试
                    stat = op.stat(test_key)
                    print(f"  ✅ 元数据: {stat.content_length} bytes")
                    
                    results[service] = "full_success"
                else:
                    print(f"  ❌ I/O 数据不匹配")
                    results[service] = "io_failed"
                    
            except Exception as e:
                print(f"  ❌ {service}: {type(e).__name__}: {e}")
                results[service] = f"error: {e}"
        
        return results
        
    except ImportError as e:
        print(f"❌ 无法导入 opendal: {e}")
        return {"import_error": str(e)}


def test_scenario_3_package_dependencies():
    """场景3: 测试包依赖关系"""
    print("\n🧪 场景3: 包依赖关系测试")
    print("-" * 50)
    
    try:
        # 检查已安装的包
        result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            installed_packages = []
            for line in result.stdout.split('\n'):
                if 'opendal' in line.lower() and line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        installed_packages.append((parts[0], parts[1]))
            
            print("📦 已安装的 OpenDAL 包:")
            for pkg, version in installed_packages:
                print(f"  {pkg} - {version}")
            
            # 检查依赖完整性
            package_names = [pkg for pkg, _ in installed_packages]
            
            dependency_check = {
                'has_opendal': 'opendal' in package_names,
                'has_core': any('core' in pkg for pkg in package_names),
                'has_database': any('database' in pkg for pkg in package_names),
                'has_cloud': any('cloud' in pkg for pkg in package_names),
                'has_advanced': any('advanced' in pkg for pkg in package_names),
            }
            
            print(f"\n🔍 依赖完整性检查:")
            for dep, exists in dependency_check.items():
                print(f"  {dep}: {'✅' if exists else '❌'}")
            
            return {
                'installed_packages': installed_packages,
                'dependency_check': dependency_check
            }
        else:
            return {"error": f"无法获取包列表: {result.stderr}"}
            
    except Exception as e:
        return {"error": str(e)}


def test_current_system_health():
    """当前系统健康检查"""
    print("\n🔍 系统健康检查")
    print("-" * 50)
    
    health_results = {}
    
    # 1. 导入测试
    print("\n📦 导入测试:")
    packages = ['opendal', 'opendal_core', 'opendal_database', 'opendal_cloud', 'opendal_advanced']
    import_results = {}
    
    for package in packages:
        try:
            __import__(package)
            import_results[package] = "✅ 成功"
            print(f"  {package}: ✅ 成功")
        except ImportError as e:
            import_results[package] = f"❌ 失败: {e}"
            print(f"  {package}: ❌ 失败: {e}")
    
    health_results['imports'] = import_results
    
    # 2. 路由测试
    try:
        import opendal
        print(f"\n🧭 路由测试:")
        
        routing_tests = [
            ('memory', 'opendal_core'),
            ('redis', 'opendal_database'),
            ('dashmap', 'opendal_cloud'),
            ('azfile', 'opendal_advanced')
        ]
        
        routing_results = {}
        for service, expected in routing_tests:
            try:
                actual = opendal._get_service_package(service)
                correct = actual == expected
                routing_results[service] = {
                    'expected': expected,
                    'actual': actual,
                    'correct': correct
                }
                print(f"  {service}: {'✅' if correct else '❌'} ({actual})")
            except Exception as e:
                routing_results[service] = {"error": str(e)}
                print(f"  {service}: ❌ 错误: {e}")
        
        health_results['routing'] = routing_results
        
    except ImportError as e:
        health_results['routing'] = {"error": f"无法导入 opendal: {e}"}
        print(f"  ❌ 无法导入 opendal: {e}")
    
    return health_results


def main():
    """主测试函数"""
    print("🚀 OpenDAL 分布式包快速场景验证")
    print("=" * 70)
    
    # 运行所有测试
    scenario_1_results = test_scenario_1_error_messages()
    scenario_2_results = test_scenario_2_installed_functionality()
    scenario_3_results = test_scenario_3_package_dependencies()
    health_results = test_current_system_health()
    
    # 汇总结果
    print(f"\n{'=' * 70}")
    print("📊 快速验证结果总结")
    print("=" * 70)
    
    final_results = {
        'scenario_1_error_messages': scenario_1_results,
        'scenario_2_functionality': scenario_2_results,
        'scenario_3_dependencies': scenario_3_results,
        'system_health': health_results
    }
    
    # 评估结果
    print(f"\n🎯 关键发现:")
    
    # 检查导入成功率
    if 'imports' in health_results:
        imports = health_results['imports']
        success_count = len([r for r in imports.values() if "✅" in r])
        total_count = len(imports)
        print(f"  包导入成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    # 检查路由正确率
    if 'routing' in health_results and isinstance(health_results['routing'], dict):
        routing = health_results['routing']
        correct_count = len([r for r in routing.values() if isinstance(r, dict) and r.get('correct', False)])
        total_routing = len([r for r in routing.values() if isinstance(r, dict)])
        if total_routing > 0:
            print(f"  路由正确率: {correct_count}/{total_routing} ({correct_count/total_routing*100:.1f}%)")
    
    # 检查功能测试
    if isinstance(scenario_2_results, dict):
        func_success = len([r for r in scenario_2_results.values() if r == "full_success"])
        func_total = len([r for r in scenario_2_results.values() if not r.startswith("import_error")])
        if func_total > 0:
            print(f"  功能测试成功率: {func_success}/{func_total} ({func_success/func_total*100:.1f}%)")
    
    # 总体评估
    print(f"\n📋 总体评估:")
    if 'imports' in health_results:
        imports = health_results['imports']
        if len([r for r in imports.values() if "✅" in r]) >= 4:
            print("  ✅ 分布式包系统基本正常工作")
            print("  ✅ 可以进行完整的可选依赖测试")
        else:
            print("  ⚠️ 分布式包系统存在问题")
            print("  ⚠️ 需要先修复基础问题")
    
    # 保存报告
    report_file = Path("quick_scenario_test_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 详细报告保存到: {report_file}")


if __name__ == "__main__":
    main()
