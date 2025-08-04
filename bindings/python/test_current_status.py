#!/usr/bin/env python3
"""
验证当前分布式包系统的状态

不依赖 uv 的依赖解析，直接测试当前环境
"""

import sys
import os
import tempfile
import json
import subprocess
from pathlib import Path


def test_current_system():
    """测试当前系统状态"""
    print("🔍 OpenDAL 分布式包系统状态检查")
    print("="*60)
    
    results = {}
    
    # 1. 检查已安装的包
    print("\n📦 检查已安装的包:")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            opendal_packages = [line.strip() for line in lines if 'opendal' in line.lower() and line.strip()]
            
            installed_packages = {}
            for pkg_line in opendal_packages:
                parts = pkg_line.split()
                if len(parts) >= 2:
                    pkg_name = parts[0]
                    version = parts[1]
                    installed_packages[pkg_name] = version
                    print(f"  ✅ {pkg_name} - {version}")
            
            results['installed_packages'] = installed_packages
            
            if not opendal_packages:
                print("  ⚠️ 未发现 OpenDAL 包")
        else:
            print(f"  ❌ 无法获取包列表: {result.stderr}")
            results['installed_packages'] = 'error'
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
        results['installed_packages'] = str(e)
    
    # 2. 测试包导入
    print("\n📥 测试包导入:")
    import_results = {}
    packages_to_test = ['opendal', 'opendal_core', 'opendal_database', 'opendal_cloud', 'opendal_advanced']
    
    for package in packages_to_test:
        try:
            __import__(package)
            import_results[package] = "✅ 成功"
            print(f"  {package}: ✅ 成功")
        except ImportError as e:
            import_results[package] = f"❌ 失败: {e}"
            print(f"  {package}: ❌ 失败: {e}")
        except Exception as e:
            import_results[package] = f"❌ 错误: {e}"
            print(f"  {package}: ❌ 错误: {e}")
    
    results['import_results'] = import_results
    
    # 3. 测试路由系统
    print("\n🧭 测试路由系统:")
    try:
        import opendal
        
        routing_tests = [
            ('memory', 'opendal_core'),
            ('fs', 'opendal_core'),
            ('redis', 'opendal_database'),
            ('dropbox', 'opendal_cloud'),
            ('azfile', 'opendal_advanced')
        ]
        
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
        
        results['routing_results'] = routing_results
        
    except ImportError as e:
        routing_error = f"❌ 无法导入 opendal: {e}"
        results['routing_results'] = routing_error
        print(f"  {routing_error}")
    
    # 4. 测试核心功能
    print("\n🔧 测试核心功能:")
    try:
        import opendal
        
        functionality_tests = [
            ('memory', {}),
            ('fs', {'root': tempfile.gettempdir()})
        ]
        
        functionality_results = {}
        for service, config in functionality_tests:
            try:
                op = opendal.Operator(service, **config)
                
                # 基本 I/O 测试
                test_key = f'test_{service}'
                test_data = b'Hello OpenDAL!'
                
                op.write(test_key, test_data)
                read_data = op.read(test_key)
                
                if read_data == test_data:
                    functionality_results[service] = "✅ 完整功能正常"
                    print(f"  {service}: ✅ 完整功能正常")
                else:
                    functionality_results[service] = f"❌ 数据不匹配"
                    print(f"  {service}: ❌ 数据不匹配")
                
            except Exception as e:
                functionality_results[service] = f"❌ 功能测试失败: {e}"
                print(f"  {service}: ❌ 功能测试失败: {e}")
        
        results['functionality_results'] = functionality_results
        
    except ImportError as e:
        functionality_error = f"❌ 无法导入 opendal: {e}"
        results['functionality_results'] = functionality_error
        print(f"  {functionality_error}")
    
    # 5. 检查包大小
    print("\n📏 检查包大小:")
    try:
        import site
        
        # 获取 site-packages 路径
        site_packages_paths = site.getsitepackages()
        if not site_packages_paths:
            site_packages_paths = [site.getusersitepackages()]
        
        size_results = {}
        total_size = 0
        
        for package in packages_to_test:
            found = False
            for sp_path in site_packages_paths:
                package_path = Path(sp_path) / package
                if package_path.exists():
                    size = sum(f.stat().st_size for f in package_path.rglob('*') if f.is_file())
                    size_mb = size / (1024 * 1024)
                    size_results[package] = f"{size_mb:.2f} MB"
                    total_size += size
                    print(f"  {package}: {size_mb:.2f} MB")
                    found = True
                    break
            
            if not found:
                size_results[package] = "未安装"
                print(f"  {package}: 未安装")
        
        total_mb = total_size / (1024 * 1024)
        size_results['total'] = f"{total_mb:.2f} MB"
        print(f"\n📊 总安装大小: {total_mb:.2f} MB")
        
        results['size_results'] = size_results
        
    except Exception as e:
        size_error = f"❌ 大小检查失败: {e}"
        results['size_results'] = size_error
        print(f"  {size_error}")
    
    # 6. 生成总结
    print(f"\n{'='*60}")
    print("📊 状态总结")
    print("="*60)
    
    # 统计导入成功的包
    successful_imports = len([r for r in import_results.values() if "✅" in r])
    total_packages = len(import_results)
    
    print(f"\n📦 包导入状态: {successful_imports}/{total_packages} ({successful_imports/total_packages*100:.1f}%)")
    
    # 统计路由成功率
    if isinstance(results.get('routing_results'), dict):
        successful_routing = len([r for r in results['routing_results'].values() if "✅" in r])
        total_routing = len(results['routing_results'])
        print(f"🧭 路由成功率: {successful_routing}/{total_routing} ({successful_routing/total_routing*100:.1f}%)")
    
    # 统计功能测试成功率
    if isinstance(results.get('functionality_results'), dict):
        successful_functionality = len([r for r in results['functionality_results'].values() if "✅" in r])
        total_functionality = len(results['functionality_results'])
        print(f"🔧 功能测试成功率: {successful_functionality}/{total_functionality} ({successful_functionality/total_functionality*100:.1f}%)")
    
    # 总体评估
    print(f"\n🎯 总体评估:")
    if successful_imports == total_packages:
        if isinstance(results.get('routing_results'), dict) and len([r for r in results['routing_results'].values() if "✅" in r]) > 0:
            print("  ✅ 分布式包系统基本工作正常")
            print("  ✅ 可以进行下一阶段测试")
        else:
            print("  ⚠️ 包导入正常，但路由系统需要检查")
    else:
        print("  ❌ 分布式包系统存在问题")
        print("  ❌ 需要先修复导入问题")
    
    # 保存报告
    report_file = Path("current_status_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 详细报告保存到: {report_file}")
    
    return results


if __name__ == "__main__":
    test_current_system()
