#!/usr/bin/env python3
"""
独立包测试脚本

测试每个服务包是否可以独立工作，不依赖其他 OpenDAL 包。
这是验证分布式架构正确性的关键测试。
"""

import subprocess
import sys
import tempfile
import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple


class IndependentPackageTest:
    def __init__(self):
        self.test_results = {}
        self.original_dir = os.getcwd()
        
    def create_isolated_environment(self, env_name: str):
        """创建一个隔离的测试环境"""
        print(f"\n🔬 创建隔离环境: {env_name}")
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix=f"opendal_isolated_{env_name}_")
        os.chdir(temp_dir)
        
        # 创建虚拟环境
        subprocess.run([sys.executable, "-m", "venv", "isolated_env"], check=True, 
                      capture_output=True)
        
        # 获取虚拟环境的路径
        if sys.platform == "win32":
            python_path = os.path.join(temp_dir, "isolated_env", "Scripts", "python.exe")
            pip_path = os.path.join(temp_dir, "isolated_env", "Scripts", "pip.exe")
        else:
            python_path = os.path.join(temp_dir, "isolated_env", "bin", "python")
            pip_path = os.path.join(temp_dir, "isolated_env", "bin", "pip")
        
        print(f"📁 隔离环境: {temp_dir}")
        return temp_dir, python_path, pip_path

    def cleanup_environment(self, temp_dir: str):
        """清理测试环境"""
        os.chdir(self.original_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_package_independence(self, package_name: str, wheel_path: str, test_services: List[Tuple[str, dict, bool]]):
        """测试单个包的独立性"""
        print(f"\n{'='*60}")
        print(f"🧪 测试包独立性: {package_name}")
        print(f"📦 Wheel 路径: {wheel_path}")
        
        temp_dir, python_path, pip_path = self.create_isolated_environment(package_name)
        
        try:
            # 1. 安装包
            print("\n📥 安装包...")
            result = subprocess.run([pip_path, "install", wheel_path], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"安装失败: {result.stderr}")
            
            print("✅ 包安装成功")
            
            # 2. 测试导入
            print("\n📦 测试导入...")
            import_test_script = f'''
try:
    import {package_name}
    print("✅ 基本导入成功")
    
    # 测试关键组件
    if hasattr({package_name}, "Operator"):
        print("✅ Operator 类可用")
    else:
        print("❌ Operator 类不可用")
        
    if hasattr({package_name}, "AsyncOperator"):
        print("✅ AsyncOperator 类可用") 
    else:
        print("❌ AsyncOperator 类不可用")
        
except Exception as e:
    print(f"❌ 导入失败: {{e}}")
    exit(1)
'''
            
            result = subprocess.run([python_path, "-c", import_test_script], 
                                  capture_output=True, text=True)
            
            import_success = result.returncode == 0
            import_output = result.stdout.strip()
            print(f"导入测试结果:\n{import_output}")
            
            if not import_success:
                raise Exception(f"导入测试失败: {result.stderr}")
            
            # 3. 测试服务功能
            print("\n🔧 测试服务功能...")
            service_results = {}
            
            for service_name, config, can_do_io in test_services:
                print(f"\n  测试服务: {service_name}")
                
                # 为了避免路径问题，将配置中的路径设置为绝对路径
                safe_config = config.copy()
                for key, value in safe_config.items():
                    if 'dir' in key.lower() and isinstance(value, str):
                        safe_config[key] = os.path.join(temp_dir, value.lstrip('/'))
                
                test_script = f'''
import sys
import os
import tempfile

try:
    import {package_name}
    
    # 测试服务创建
    config = {safe_config}
    op = {package_name}.Operator("{service_name}", **config)
    print("✅ Operator 创建成功")
    
    if {can_do_io}:
        # 测试 I/O 功能
        try:
            test_key = "test_key_isolated"
            test_data = b"Hello from isolated test!"
            
            # 写入
            op.write(test_key, test_data)
            print("✅ 写入成功")
            
            # 读取
            read_data = op.read(test_key)
            if read_data == test_data:
                print("✅ 读取验证成功")
            else:
                print(f"❌ 数据不匹配: {{read_data}} != {{test_data}}")
            
            # 元数据
            stat = op.stat(test_key)
            print(f"✅ 元数据获取成功: 大小={{stat.content_length}}")
            
            # 清理
            try:
                op.delete(test_key)
                print("✅ 删除成功")
            except:
                print("⚠️ 删除失败（可能不支持）")
                
        except Exception as io_e:
            print(f"❌ I/O 测试失败: {{io_e}}")
    else:
        print("⚠️ 仅配置验证（需要外部服务）")
        
except Exception as e:
    print(f"❌ 服务测试失败: {{e}}")
    import traceback
    traceback.print_exc()
'''
                
                result = subprocess.run([python_path, "-c", test_script], 
                                      capture_output=True, text=True)
                
                service_output = result.stdout.strip()
                service_success = result.returncode == 0 and "✅" in service_output
                
                service_results[service_name] = {
                    'success': service_success,
                    'output': service_output,
                    'error': result.stderr if result.stderr else None
                }
                
                print(f"    结果: {'✅ 成功' if service_success else '❌ 失败'}")
                if service_output:
                    for line in service_output.split('\n'):
                        if line.strip():
                            print(f"    {line}")
            
            # 4. 汇总结果
            total_services = len(test_services)
            successful_services = len([r for r in service_results.values() if r['success']])
            
            package_result = {
                'package_name': package_name,
                'wheel_path': wheel_path,
                'import_success': import_success,
                'import_output': import_output,
                'service_results': service_results,
                'success_rate': f"{successful_services}/{total_services}",
                'overall_success': import_success and successful_services > 0
            }
            
            self.test_results[package_name] = package_result
            
            print(f"\n📊 {package_name} 独立性测试摘要:")
            print(f"  导入: {'✅' if import_success else '❌'}")
            print(f"  服务成功率: {successful_services}/{total_services}")
            print(f"  整体状态: {'✅ 通过' if package_result['overall_success'] else '❌ 失败'}")
            
        except Exception as e:
            error_result = {
                'package_name': package_name,
                'wheel_path': wheel_path,
                'error': str(e),
                'overall_success': False
            }
            self.test_results[package_name] = error_result
            print(f"\n❌ {package_name} 测试失败: {e}")
        
        finally:
            self.cleanup_environment(temp_dir)

    def run_all_independence_tests(self):
        """运行所有独立性测试"""
        print("🚀 OpenDAL 独立包测试")
        print("="*60)
        print("目标: 验证每个服务包可以独立工作，不依赖其他 OpenDAL 包")
        
        # 定义测试配置
        test_configs = [
            {
                'package_name': 'opendal_core',
                'wheel_path': '/Users/wang/i/opendal/bindings/python/packages/opendal-core/dist/opendal_core-0.46.0-cp311-cp311-macosx_11_0_arm64.whl',
                'test_services': [
                    ('memory', {}, True),  # 内存存储，可以完整测试
                    ('fs', {'root': 'test_fs'}, True),  # 文件系统，可以完整测试
                    ('http', {'endpoint': 'https://httpbin.org/'}, False),  # HTTP，仅配置验证
                ]
            },
            {
                'package_name': 'opendal_database',
                'wheel_path': '/Users/wang/i/opendal/bindings/python/packages/opendal-database/dist/opendal_database-0.46.0-cp311-cp311-macosx_11_0_arm64.whl',
                'test_services': [
                    ('sled', {'datadir': 'test_sled'}, True),  # 本地存储，可以完整测试
                    ('redb', {'datadir': 'test_redb', 'table': 'test_table'}, True),  # 修复配置
                    ('persy', {'datadir': 'test_persy', 'datafile': 'test.persy'}, True),  # 修复配置
                    ('redis', {'endpoint': 'redis://localhost:6379'}, False),  # 需要 Redis 服务
                    ('sqlite', {'connection_string': 'sqlite:///test.db', 'table': 'test_table'}, False),  # 需要 SQLite 配置
                ]
            },
            {
                'package_name': 'opendal_cloud',
                'wheel_path': '/Users/wang/i/opendal/bindings/python/packages/opendal-cloud/dist/opendal_cloud-0.46.0-cp311-cp311-macosx_11_0_arm64.whl',
                'test_services': [
                    ('dashmap', {}, True),  # 内存存储，可以完整测试
                    ('moka', {}, True),  # 内存缓存，可以完整测试
                    ('dropbox', {'access_token': 'test_token'}, False),  # 需要凭证
                    ('b2', {'bucket': 'test', 'application_key_id': 'test', 'application_key': 'test'}, False),  # 需要凭证
                ]
            },
            {
                'package_name': 'opendal_advanced',
                'wheel_path': '/Users/wang/i/opendal/bindings/python/packages/opendal-advanced/dist/opendal_advanced-0.46.0-cp311-cp311-macosx_11_0_arm64.whl',
                'test_services': [
                    ('cacache', {'datadir': 'test_cacache'}, True),  # 本地缓存，可以完整测试
                    ('azfile', {'endpoint': 'https://test.file.core.windows.net', 'share_name': 'test'}, False),  # 需要凭证
                    ('monoiofs', {'dir': 'test_monoio'}, False),  # 可能需要特殊配置
                ]
            }
        ]
        
        # 运行每个包的测试
        for config in test_configs:
            # 检查 wheel 文件是否存在
            if not Path(config['wheel_path']).exists():
                print(f"\n❌ Wheel 文件不存在: {config['wheel_path']}")
                self.test_results[config['package_name']] = {
                    'package_name': config['package_name'],
                    'error': f"Wheel 文件不存在: {config['wheel_path']}",
                    'overall_success': False
                }
                continue
                
            self.test_package_independence(
                config['package_name'],
                config['wheel_path'],
                config['test_services']
            )
        
        # 生成最终报告
        self.generate_independence_report()

    def generate_independence_report(self):
        """生成独立性测试报告"""
        print(f"\n{'='*60}")
        print("📊 独立包测试报告")
        print("="*60)
        
        total_packages = len(self.test_results)
        successful_packages = len([r for r in self.test_results.values() if r.get('overall_success', False)])
        
        print(f"\n📦 包独立性概览:")
        print(f"  总包数: {total_packages}")
        print(f"  成功包数: {successful_packages}")
        print(f"  成功率: {successful_packages/total_packages*100:.1f}%")
        
        print(f"\n📋 详细结果:")
        for package_name, result in self.test_results.items():
            status = "✅ 通过" if result.get('overall_success', False) else "❌ 失败"
            print(f"\n🔸 {package_name}: {status}")
            
            if 'success_rate' in result:
                print(f"   服务成功率: {result['success_rate']}")
            
            if 'error' in result:
                print(f"   错误: {result['error']}")
            
            if 'service_results' in result:
                print(f"   服务详情:")
                for service, service_result in result['service_results'].items():
                    service_status = "✅" if service_result['success'] else "❌"
                    print(f"     {service}: {service_status}")
        
        # 关键发现
        print(f"\n🔍 关键发现:")
        
        if successful_packages == total_packages:
            print("  ✅ 所有包都可以独立工作")
            print("  ✅ 分布式架构验证成功")
        elif successful_packages > 0:
            print(f"  ⚠️ {successful_packages}/{total_packages} 包可以独立工作")
            print("  ⚠️ 需要修复部分包的独立性问题")
        else:
            print("  ❌ 没有包可以独立工作")
            print("  ❌ 分布式架构需要重大修复")
        
        # 保存详细报告
        report_file = Path("/Users/wang/i/opendal/bindings/python/tests/independence_test_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return successful_packages == total_packages


if __name__ == "__main__":
    tester = IndependentPackageTest()
    success = tester.run_all_independence_tests()
    
    if success:
        print("\n🎉 所有包独立性测试通过！")
        sys.exit(0)
    else:
        print("\n💥 独立性测试存在问题，需要修复")
        sys.exit(1)
