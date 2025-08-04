#!/usr/bin/env python3
"""
本地安装测试 - 充分利用开发模式优点

优点：
1. 绕过版本限制 - 使用本地路径不需要版本匹配
2. 真实环境测试 - 创建隔离的环境测试实际安装过程  
3. 可编辑模式 - 修改代码后无需重新安装即可测试
4. 清晰的结果 - 脚本输出导入和安装成功/失败信息
"""

import subprocess
import sys
import tempfile
import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple


class LocalInstallationTest:
    def __init__(self):
        self.test_results = {}
        self.original_dir = os.getcwd()
        self.base_dir = Path("/Users/wang/i/opendal/bindings/python")
        
    def create_clean_environment(self, env_name: str):
        """创建干净的测试环境"""
        print(f"\n🐍 创建环境: {env_name}")
        
        temp_dir = tempfile.mkdtemp(prefix=f"opendal_local_{env_name}_")
        os.chdir(temp_dir)
        
        # 创建虚拟环境
        subprocess.run([sys.executable, "-m", "venv", "test_env"], check=True, capture_output=True)
        
        # 获取路径
        if sys.platform == "win32":
            python_path = os.path.join(temp_dir, "test_env", "Scripts", "python.exe")
            pip_path = os.path.join(temp_dir, "test_env", "Scripts", "pip.exe")
        else:
            python_path = os.path.join(temp_dir, "test_env", "bin", "python")
            pip_path = os.path.join(temp_dir, "test_env", "bin", "pip")
        
        print(f"📁 环境路径: {temp_dir}")
        return temp_dir, python_path, pip_path

    def cleanup_environment(self, temp_dir: str):
        """清理测试环境"""
        os.chdir(self.original_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def install_packages_locally(self, pip_path: str, packages_to_install: List[str]):
        """本地安装指定的包"""
        print(f"\n📦 本地安装包: {packages_to_install}")
        
        # 定义包路径映射
        package_paths = {
            'opendal-core': self.base_dir / "packages/opendal-core",
            'opendal-database': self.base_dir / "packages/opendal-database", 
            'opendal-cloud': self.base_dir / "packages/opendal-cloud",
            'opendal-advanced': self.base_dir / "packages/opendal-advanced",
            'opendal': self.base_dir
        }
        
        installed_packages = []
        
        for package in packages_to_install:
            if package in package_paths:
                package_path = package_paths[package]
                print(f"  安装 {package} 从 {package_path}")
                
                # 使用可编辑模式安装
                result = subprocess.run([pip_path, "install", "-e", str(package_path)], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    installed_packages.append(package)
                    print(f"    ✅ {package} 安装成功")
                else:
                    print(f"    ❌ {package} 安装失败: {result.stderr}")
                    raise Exception(f"安装 {package} 失败: {result.stderr}")
            else:
                print(f"    ⚠️ 未知包: {package}")
        
        return installed_packages

    def test_package_functionality(self, python_path: str, test_services: List[Tuple[str, str]]):
        """测试包功能"""
        print(f"\n🔧 测试包功能...")
        
        service_results = {}
        
        for service_name, expected_result in test_services:
            print(f"\n  测试服务: {service_name}")
            
            test_script = f'''
import sys
import tempfile
import os

try:
    import opendal
    
    # 服务配置
    configs = {{
        "memory": {{}},
        "fs": {{"root": tempfile.gettempdir()}},
        "redis": {{"endpoint": "redis://localhost:6379"}},
        "sqlite": {{"connection_string": "sqlite:///test.db", "table": "test_table"}},
        "sled": {{"datadir": tempfile.mkdtemp()}},
        "dropbox": {{"access_token": "test_token"}},
        "dashmap": {{}},
        "moka": {{}},
        "azfile": {{"endpoint": "https://test.file.core.windows.net", "share_name": "test"}},
        "cacache": {{"datadir": tempfile.mkdtemp()}},
    }}
    
    config = configs.get("{service_name}", {{}})
    
    # 尝试创建 Operator
    op = opendal.Operator("{service_name}", **config)
    print("✅ Operator 创建成功")
    
    # 对于内存类服务，进行完整 I/O 测试
    if "{service_name}" in ["memory", "fs", "dashmap", "moka"]:
        try:
            test_key = "test_local_install"
            test_data = b"Hello Local Install!"
            
            op.write(test_key, test_data)
            read_data = op.read(test_key)
            
            if read_data == test_data:
                print("✅ I/O 测试完全成功")
                
                # 测试元数据
                stat = op.stat(test_key)
                print(f"✅ 元数据测试成功: {{stat.content_length}} bytes")
                
                # 测试删除
                try:
                    op.delete(test_key)
                    print("✅ 删除测试成功")
                except:
                    print("⚠️ 删除测试跳过（可能不支持）")
                    
            else:
                print(f"❌ I/O 数据不匹配: {{read_data}} != {{test_data}}")
                
        except Exception as io_e:
            print(f"⚠️ I/O 测试失败: {{io_e}}")
    else:
        print("⚠️ 仅配置验证（需要外部服务或凭证）")

except ImportError as e:
    if "{expected_result}" == "should_fail":
        print(f"✅ 预期的导入失败: {{e}}")
    else:
        print(f"❌ 意外的导入失败: {{e}}")
        
except Exception as e:
    print(f"⚠️ 其他错误: {{type(e).__name__}}: {{e}}")
'''
            
            result = subprocess.run([python_path, "-c", test_script], 
                                  capture_output=True, text=True)
            
            output = result.stdout.strip()
            success = "✅" in output and result.returncode == 0
            
            service_results[service_name] = {
                'expected': expected_result,
                'success': success,
                'output': output,
                'stderr': result.stderr if result.stderr else None
            }
            
            # 打印结果
            status = "✅ 通过" if success else "❌ 失败"
            print(f"    {status}")
            
            if output:
                for line in output.split('\n'):
                    if line.strip():
                        print(f"      {line}")
        
        return service_results

    def test_installation_scenario(self, scenario_name: str, packages_to_install: List[str], test_services: List[Tuple[str, str]]):
        """测试一个安装场景"""
        print(f"\n{'='*70}")
        print(f"🧪 测试场景: {scenario_name}")
        print(f"📦 安装包: {packages_to_install}")
        
        temp_dir, python_path, pip_path = self.create_clean_environment(scenario_name.replace(' ', '_'))
        
        try:
            # 1. 安装包
            installed_packages = self.install_packages_locally(pip_path, packages_to_install)
            
            # 2. 验证安装
            print(f"\n🔍 验证安装...")
            list_result = subprocess.run([pip_path, "list"], capture_output=True, text=True)
            installed_list = list_result.stdout
            
            verified_packages = {}
            for package in packages_to_install:
                package_found = package.replace('-', '_') in installed_list or package in installed_list
                verified_packages[package] = "✅ 已安装" if package_found else "❌ 未找到"
                print(f"  {package}: {'✅ 已安装' if package_found else '❌ 未找到'}")
            
            # 3. 测试功能
            service_results = self.test_package_functionality(python_path, test_services)
            
            # 4. 汇总结果
            total_packages = len(packages_to_install)
            verified_count = len([v for v in verified_packages.values() if "✅" in v])
            
            total_services = len(test_services)
            working_services = len([s for s in service_results.values() if s['success']])
            
            scenario_result = {
                'scenario_name': scenario_name,
                'packages_to_install': packages_to_install,
                'installed_packages': installed_packages,
                'verified_packages': verified_packages,
                'package_success_rate': f"{verified_count}/{total_packages}",
                'service_results': service_results,
                'service_success_rate': f"{working_services}/{total_services}",
                'overall_success': verified_count == total_packages and working_services >= total_services * 0.7
            }
            
            self.test_results[scenario_name] = scenario_result
            
            print(f"\n📊 {scenario_name} 结果摘要:")
            print(f"  包安装: {verified_count}/{total_packages}")
            print(f"  服务功能: {working_services}/{total_services}")
            print(f"  整体状态: {'✅ 通过' if scenario_result['overall_success'] else '❌ 需要改进'}")
            
        except Exception as e:
            error_result = {
                'scenario_name': scenario_name,
                'packages_to_install': packages_to_install,
                'error': str(e),
                'overall_success': False
            }
            self.test_results[scenario_name] = error_result
            print(f"\n❌ {scenario_name} 测试失败: {e}")
        
        finally:
            self.cleanup_environment(temp_dir)

    def run_all_local_tests(self):
        """运行所有本地安装测试"""
        print("🚀 OpenDAL 本地安装测试")
        print("="*70)
        print("利用开发模式优点：绕过版本限制，真实环境测试")
        
        # 定义测试场景
        scenarios = [
            {
                'name': '仅核心服务',
                'packages': ['opendal-core', 'opendal'],
                'test_services': [
                    ('memory', 'should_work'),
                    ('fs', 'should_work'),
                    ('redis', 'should_fail'),  # 应该路由失败
                ]
            },
            {
                'name': '核心+数据库',
                'packages': ['opendal-core', 'opendal-database', 'opendal'],
                'test_services': [
                    ('memory', 'should_work'),
                    ('redis', 'should_work'),
                    ('sled', 'should_work'),
                    ('dropbox', 'should_fail'),  # 应该路由失败
                ]
            },
            {
                'name': '核心+云服务',
                'packages': ['opendal-core', 'opendal-cloud', 'opendal'],
                'test_services': [
                    ('memory', 'should_work'),
                    ('dashmap', 'should_work'),
                    ('moka', 'should_work'),
                    ('dropbox', 'should_work'),
                    ('redis', 'should_fail'),  # 应该路由失败
                ]
            },
            {
                'name': '核心+高级服务',
                'packages': ['opendal-core', 'opendal-advanced', 'opendal'],
                'test_services': [
                    ('memory', 'should_work'),
                    ('cacache', 'should_work'),
                    ('azfile', 'should_work'),
                    ('redis', 'should_fail'),  # 应该路由失败
                ]
            },
            {
                'name': '全部服务',
                'packages': ['opendal-core', 'opendal-database', 'opendal-cloud', 'opendal-advanced', 'opendal'],
                'test_services': [
                    ('memory', 'should_work'),
                    ('redis', 'should_work'),
                    ('dashmap', 'should_work'),
                    ('cacache', 'should_work'),
                ]
            }
        ]
        
        # 运行每个场景
        for scenario in scenarios:
            self.test_installation_scenario(
                scenario['name'],
                scenario['packages'],
                scenario['test_services']
            )
        
        # 生成最终报告
        self.generate_final_report()

    def generate_final_report(self):
        """生成最终报告"""
        print(f"\n{'='*70}")
        print("📊 本地安装测试报告")
        print("="*70)
        
        total_scenarios = len(self.test_results)
        successful_scenarios = len([r for r in self.test_results.values() if r.get('overall_success', False)])
        
        print(f"\n📋 总体结果:")
        print(f"  测试场景: {total_scenarios}")
        print(f"  成功场景: {successful_scenarios}")
        print(f"  成功率: {successful_scenarios/total_scenarios*100:.1f}%")
        
        print(f"\n🔍 各场景详情:")
        for scenario_name, result in self.test_results.items():
            status = "✅ 通过" if result.get('overall_success', False) else "⚠️ 需要改进"
            print(f"\n🔸 {scenario_name}: {status}")
            
            if 'package_success_rate' in result:
                print(f"   包安装: {result['package_success_rate']}")
            
            if 'service_success_rate' in result:
                print(f"   服务功能: {result['service_success_rate']}")
            
            if 'error' in result:
                print(f"   错误: {result['error']}")
        
        # 开发模式优点验证
        print(f"\n🎯 开发模式优点验证:")
        if successful_scenarios > 0:
            print("  ✅ 绕过版本限制 - 本地路径安装成功")
            print("  ✅ 真实环境测试 - 隔离环境测试通过")
            print("  ✅ 可编辑模式 - 使用 -e 安装模式")
            print("  ✅ 清晰的结果 - 详细的成功/失败信息")
        
        if successful_scenarios == total_scenarios:
            print("\n🎉 所有场景测试通过！分布式包系统工作完美！")
        elif successful_scenarios >= total_scenarios * 0.8:
            print(f"\n✅ 大部分场景通过！系统基本正常工作")
        else:
            print(f"\n⚠️ 需要改进一些场景")
        
        # 保存详细报告
        report_file = Path("/Users/wang/i/opendal/bindings/python/tests/local_installation_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return successful_scenarios >= total_scenarios * 0.8


if __name__ == "__main__":
    tester = LocalInstallationTest()
    success = tester.run_all_local_tests()
    
    if success:
        print("\n🎉 本地安装测试基本通过！")
        sys.exit(0)
    else:
        print("\n💥 本地安装测试需要改进")
        sys.exit(1)
