#!/usr/bin/env python3
"""
快速验证当前状态的测试

验证我们当前分布式包的工作状态
"""

import json
import os
import tempfile
from pathlib import Path


def test_current_installation():
    """测试当前安装状态"""
    print("🔍 当前安装状态检查")
    print("="*50)
    
    results = {}
    
    # 1. 检查已安装的包
    try:
        import subprocess
        result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            opendal_packages = [line for line in result.stdout.split('\n') if 'opendal' in line.lower()]
            print("📦 已安装的 OpenDAL 包:")
            for pkg in opendal_packages:
                print(f"  {pkg}")
            results['installed_packages'] = opendal_packages
        else:
            print("❌ 无法获取包列表")
            results['installed_packages'] = "error"
    except Exception as e:
        print(f"❌ 包检查失败: {e}")
        results['installed_packages'] = str(e)
    
    # 2. 测试基本导入
    print("\n📦 基本导入测试:")
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
    
    results['import_tests'] = import_results
    
    # 3. 测试核心功能
    print("\n🔧 核心功能测试:")
    functionality_results = {}
    
    try:
        import opendal
        
        # 测试基本服务
        basic_services = [
            ('memory', {}),
            ('fs', {'root': tempfile.gettempdir()})
        ]
        
        for service, config in basic_services:
            try:
                op = opendal.Operator(service, **config)
                
                # 基本 I/O 测试
                test_key = f'test_{service}'
                op.write(test_key, b'Hello!')
                data = op.read(test_key)
                assert data == b'Hello!'
                
                functionality_results[service] = "✅ 完整测试通过"
                print(f"  {service}: ✅ 完整测试通过")
                
            except Exception as e:
                functionality_results[service] = f"❌ 失败: {e}"
                print(f"  {service}: ❌ 失败: {e}")
        
        # 测试路由
        routing_tests = [
            ('redis', 'opendal_database'),
            ('dropbox', 'opendal_cloud'),
            ('azfile', 'opendal_advanced')
        ]
        
        print("\n🧭 路由测试:")
        routing_results = {}
        
        for service, expected_package in routing_tests:
            try:
                actual_package = opendal._get_service_package(service)
                if actual_package == expected_package:
                    routing_results[service] = f"✅ 正确路由到 {expected_package}"
                    print(f"  {service}: ✅ 正确路由到 {expected_package}")
                else:
                    routing_results[service] = f"❌ 错误路由: 期望 {expected_package}, 实际 {actual_package}"
                    print(f"  {service}: ❌ 错误路由: 期望 {expected_package}, 实际 {actual_package}")
            except Exception as e:
                routing_results[service] = f"❌ 路由失败: {e}"
                print(f"  {service}: ❌ 路由失败: {e}")
        
        results['routing_tests'] = routing_results
        
    except ImportError as e:
        functionality_results['import_error'] = f"❌ 无法导入 opendal: {e}"
        print(f"  ❌ 无法导入 opendal: {e}")
    
    results['functionality_tests'] = functionality_results
    
    # 4. 测试包大小
    print("\n📏 包大小分析:")
    try:
        import site
        site_packages = site.getsitepackages()[0] if site.getsitepackages() else site.getusersitepackages()
        
        size_results = {}
        total_size = 0
        
        for package in packages:
            package_path = Path(site_packages) / package
            if package_path.exists():
                size = sum(f.stat().st_size for f in package_path.rglob('*') if f.is_file())
                size_mb = size / (1024 * 1024)
                size_results[package] = f"{size_mb:.2f} MB"
                total_size += size
                print(f"  {package}: {size_mb:.2f} MB")
            else:
                size_results[package] = "不存在"
                print(f"  {package}: 不存在")
        
        total_mb = total_size / (1024 * 1024)
        size_results['total'] = f"{total_mb:.2f} MB"
        print(f"\n📊 总大小: {total_mb:.2f} MB")
        
        results['size_analysis'] = size_results
        
    except Exception as e:
        results['size_analysis'] = f"❌ 大小分析失败: {e}"
        print(f"  ❌ 大小分析失败: {e}")
    
    # 5. 生成报告
    print(f"\n{'='*50}")
    print("📊 测试结果摘要")
    print("="*50)
    
    # 导入成功率
    import_success = len([r for r in import_results.values() if '✅' in r])
    print(f"包导入成功率: {import_success}/{len(import_results)} ({import_success/len(import_results)*100:.1f}%)")
    
    # 功能测试成功率
    if 'routing_tests' in results:
        routing_success = len([r for r in results['routing_tests'].values() if '✅' in r])
        print(f"路由测试成功率: {routing_success}/{len(results['routing_tests'])} ({routing_success/len(results['routing_tests'])*100:.1f}%)")
    
    # 总体状态
    if import_success == len(import_results):
        print("\n✅ 分布式包系统基本工作正常")
    else:
        print("\n⚠️ 分布式包系统存在问题，需要修复")
    
    # 保存详细报告
    report_file = Path("/Users/wang/i/opendal/bindings/python/tests/current_state_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 详细报告保存到: {report_file}")
    
    return results


if __name__ == "__main__":
    test_current_installation()
