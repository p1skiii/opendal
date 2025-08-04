#!/usr/bin/env python3
"""
可选依赖三大关键场景测试

场景1: 未安装可选依赖的行为 - 验证错误提示
场景2: 安装可选依赖的功能 - 验证 pip install opendal[database] 
场景3: 多个可选依赖组合 - 验证 pip install opendal[database,cloud]
"""

import subprocess
import sys
import tempfile
import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple


class OptionalDependencyScenarios:
    def __init__(self):
        self.test_results = {}
        self.original_dir = os.getcwd()
        self.base_dir = Path("/Users/wang/i/opendal/bindings/python")
        
    def create_test_environment(self, scenario_name: str):
        """创建测试环境"""
        print(f"\n🐍 创建环境: {scenario_name}")
        
        temp_dir = tempfile.mkdtemp(prefix=f"opendal_scenario_{scenario_name}_")
        os.chdir(temp_dir)
        
        # 创建虚拟环境
        subprocess.run([sys.executable, "-m", "venv", "env"], check=True, capture_output=True)
        
        # 获取路径
        if sys.platform == "win32":
            python_path = os.path.join(temp_dir, "env", "Scripts", "python.exe")
            pip_path = os.path.join(temp_dir, "env", "Scripts", "pip.exe")
        else:
            python_path = os.path.join(temp_dir, "env", "bin", "python")
            pip_path = os.path.join(temp_dir, "env", "bin", "pip")
        
        print(f"📁 环境: {temp_dir}")
        return temp_dir, python_path, pip_path

    def cleanup_environment(self, temp_dir: str):
        """清理环境"""
        os.chdir(self.original_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def install_base_packages(self, pip_path: str):
        """安装基础包（为可选依赖测试做准备）"""
        print("📦 安装基础包...")
        
        # 首先安装所有子包，但不安装元包
        packages = [
            self.base_dir / "packages/opendal-core",
            self.base_dir / "packages/opendal-database", 
            self.base_dir / "packages/opendal-cloud",
            self.base_dir / "packages/opendal-advanced"
        ]
        
        for package_path in packages:
            result = subprocess.run([pip_path, "install", "-e", str(package_path)], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"安装 {package_path.name} 失败: {result.stderr}")
            print(f"  ✅ {package_path.name}")

    def scenario_1_missing_dependencies(self):
        """场景1: 未安装可选依赖的行为测试"""
        print(f"\n{'='*70}")
        print("🧪 场景1: 未安装可选依赖的行为测试")
        print("目标: 验证缺少依赖时的错误提示是否有用")
        
        temp_dir, python_path, pip_path = self.create_test_environment("missing_deps")
        
        try:
            # 1. 只安装核心包和元包
            print("\n📦 只安装核心包...")
            core_package = self.base_dir / "packages/opendal-core"
            meta_package = self.base_dir
            
            # 安装核心包
            result = subprocess.run([pip_path, "install", "-e", str(core_package)], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"安装核心包失败: {result.stderr}")
            
            # 安装元包（不带可选依赖）
            result = subprocess.run([pip_path, "install", "-e", str(meta_package)], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"安装元包失败: {result.stderr}")
            
            print("✅ 核心包安装完成")
            
            # 2. 验证已安装的包
            list_result = subprocess.run([pip_path, "list"], capture_output=True, text=True)
            installed_packages = list_result.stdout
            print(f"\n📋 已安装包:")
            for line in installed_packages.split('\n'):
                if 'opendal' in line.lower() and line.strip():
                    print(f"  {line.strip()}")
            
            # 3. 测试缺少依赖时的行为
            print(f"\n🚨 测试缺少依赖时的行为:")
            
            error_test_cases = [
                ('redis', 'database'),
                ('sqlite', 'database'), 
                ('dropbox', 'cloud'),
                ('dashmap', 'cloud'),
                ('azfile', 'advanced'),
                ('cacache', 'advanced')
            ]
            
            error_results = {}
            
            for service, expected_package_type in error_test_cases:
                print(f"\n  测试 {service} (期望提示安装 {expected_package_type}):")
                
                test_script = f'''
try:
    import opendal
    
    # 尝试使用需要额外依赖的服务
    if "{service}" == "redis":
        config = {{"endpoint": "redis://localhost:6379"}}
    elif "{service}" == "sqlite":
        config = {{"connection_string": "sqlite:///test.db", "table": "test_table"}}
    elif "{service}" == "dropbox":
        config = {{"access_token": "test_token"}}
    elif "{service}" == "dashmap":
        config = {{}}
    elif "{service}" == "azfile":
        config = {{"endpoint": "https://test.file.core.windows.net", "share_name": "test"}}
    elif "{service}" == "cacache":
        config = {{"datadir": "/tmp/cache"}}
    else:
        config = {{}}
    
    op = opendal.Operator("{service}", **config)
    print("❌ 意外成功: 应该失败但却成功了")
    
except ImportError as e:
    print(f"✅ 正确的导入错误: {{e}}")
    
    # 检查错误消息是否有用
    error_msg = str(e).lower()
    if "{expected_package_type}" in error_msg or "install" in error_msg:
        print("✅ 错误消息包含有用信息")
    else:
        print("⚠️ 错误消息不够有用")
        
except Exception as e:
    print(f"⚠️ 其他类型错误: {{type(e).__name__}}: {{e}}")
'''
                
                result = subprocess.run([python_path, "-c", test_script], 
                                      capture_output=True, text=True)
                
                output = result.stdout.strip()
                has_useful_error = "正确的导入错误" in output and "有用信息" in output
                
                error_results[service] = {
                    'expected_package_type': expected_package_type,
                    'has_useful_error': has_useful_error,
                    'output': output
                }
                
                if output:
                    for line in output.split('\n'):
                        if line.strip():
                            print(f"    {line}")
            
            # 4. 汇总场景1结果
            useful_errors = len([r for r in error_results.values() if r['has_useful_error']])
            total_tests = len(error_results)
            
            scenario_1_result = {
                'scenario': 'missing_dependencies',
                'error_results': error_results,
                'useful_error_rate': f"{useful_errors}/{total_tests}",
                'success': useful_errors >= total_tests * 0.5  # 至少一半的错误是有用的
            }
            
            self.test_results['scenario_1'] = scenario_1_result
            
            print(f"\n📊 场景1结果:")
            print(f"  有用错误率: {useful_errors}/{total_tests}")
            print(f"  状态: {'✅ 通过' if scenario_1_result['success'] else '❌ 需要改进'}")
            
        except Exception as e:
            self.test_results['scenario_1'] = {
                'scenario': 'missing_dependencies',
                'error': str(e),
                'success': False
            }
            print(f"\n❌ 场景1失败: {e}")
        
        finally:
            self.cleanup_environment(temp_dir)

    def scenario_2_single_optional_dependency(self):
        """场景2: 安装可选依赖的功能测试"""
        print(f"\n{'='*70}")
        print("🧪 场景2: 安装可选依赖的功能测试")
        print("目标: 验证 pip install opendal[database] 功能")
        
        temp_dir, python_path, pip_path = self.create_test_environment("single_optional")
        
        try:
            # 1. 安装基础包
            self.install_base_packages(pip_path)
            
            # 2. 安装带数据库扩展的元包
            print(f"\n📦 安装 opendal[database]...")
            
            # 首先构建最新的元包
            build_result = subprocess.run(["python", "-m", "build", "--wheel"], 
                                        cwd=str(self.base_dir), capture_output=True, text=True)
            if build_result.returncode != 0:
                raise Exception(f"构建元包失败: {build_result.stderr}")
            
            # 找到最新的元包
            dist_dir = self.base_dir / "dist"
            meta_wheels = list(dist_dir.glob("opendal-*.whl"))
            if not meta_wheels:
                raise Exception("未找到元包wheel")
            
            latest_wheel = max(meta_wheels, key=lambda p: p.stat().st_mtime)
            
            # 安装带可选依赖的包
            install_cmd = [pip_path, "install", f"{latest_wheel}[database]"]
            result = subprocess.run(install_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"⚠️ wheel安装失败，尝试可编辑模式...")
                # 尝试可编辑模式
                install_cmd = [pip_path, "install", "-e", f"{self.base_dir}[database]"]
                result = subprocess.run(install_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    raise Exception(f"安装失败: {result.stderr}")
            
            print("✅ opendal[database] 安装成功")
            
            # 3. 验证安装的包
            print(f"\n🔍 验证安装的包:")
            list_result = subprocess.run([pip_path, "list"], capture_output=True, text=True)
            installed_list = list_result.stdout
            
            expected_packages = ['opendal', 'opendal-core', 'opendal-database']
            package_check = {}
            
            for pkg in expected_packages:
                found = pkg.replace('-', '_') in installed_list or pkg in installed_list
                package_check[pkg] = found
                print(f"  {pkg}: {'✅ 已安装' if found else '❌ 未安装'}")
            
            # 4. 测试数据库服务功能
            print(f"\n🔧 测试数据库服务功能:")
            
            database_services = [
                ('redis', '配置验证'),
                ('sqlite', '配置验证'),
                ('sled', '完整功能')
            ]
            
            service_results = {}
            
            for service, test_type in database_services:
                print(f"\n  测试 {service} ({test_type}):")
                
                test_script = f'''
import tempfile
import os

try:
    import opendal
    
    # 服务配置
    if "{service}" == "redis":
        config = {{"endpoint": "redis://localhost:6379"}}
    elif "{service}" == "sqlite":
        config = {{"connection_string": "sqlite:///test.db", "table": "test_table"}}
    elif "{service}" == "sled":
        config = {{"datadir": tempfile.mkdtemp()}}
    else:
        config = {{}}
    
    op = opendal.Operator("{service}", **config)
    print("✅ Operator 创建成功")
    
    # 对于sled，尝试完整的I/O操作
    if "{service}" == "sled":
        try:
            test_key = "scenario2_test"
            test_data = b"Database test data"
            
            op.write(test_key, test_data)
            read_data = op.read(test_key)
            
            if read_data == test_data:
                print("✅ 完整I/O测试成功")
            else:
                print("❌ I/O数据不匹配")
                
        except Exception as io_e:
            print(f"⚠️ I/O测试失败: {{io_e}}")
    else:
        print("✅ 配置验证通过")

except Exception as e:
    print(f"❌ 测试失败: {{type(e).__name__}}: {{e}}")
'''
                
                result = subprocess.run([python_path, "-c", test_script], 
                                      capture_output=True, text=True)
                
                output = result.stdout.strip()
                success = "✅" in output and result.returncode == 0
                
                service_results[service] = {
                    'test_type': test_type,
                    'success': success,
                    'output': output
                }
                
                if output:
                    for line in output.split('\n'):
                        if line.strip():
                            print(f"    {line}")
            
            # 5. 汇总场景2结果
            packages_installed = len([p for p in package_check.values() if p])
            services_working = len([s for s in service_results.values() if s['success']])
            
            scenario_2_result = {
                'scenario': 'single_optional_dependency',
                'package_check': package_check,
                'service_results': service_results,
                'packages_success_rate': f"{packages_installed}/{len(expected_packages)}",
                'services_success_rate': f"{services_working}/{len(database_services)}",
                'success': packages_installed == len(expected_packages) and services_working >= len(database_services) * 0.7
            }
            
            self.test_results['scenario_2'] = scenario_2_result
            
            print(f"\n📊 场景2结果:")
            print(f"  包安装: {packages_installed}/{len(expected_packages)}")
            print(f"  服务功能: {services_working}/{len(database_services)}")
            print(f"  状态: {'✅ 通过' if scenario_2_result['success'] else '❌ 需要改进'}")
            
        except Exception as e:
            self.test_results['scenario_2'] = {
                'scenario': 'single_optional_dependency',
                'error': str(e),
                'success': False
            }
            print(f"\n❌ 场景2失败: {e}")
        
        finally:
            self.cleanup_environment(temp_dir)

    def scenario_3_multiple_optional_dependencies(self):
        """场景3: 多个可选依赖组合测试"""
        print(f"\n{'='*70}")
        print("🧪 场景3: 多个可选依赖组合测试")
        print("目标: 验证 pip install opendal[database,cloud] 功能")
        
        temp_dir, python_path, pip_path = self.create_test_environment("multiple_optional")
        
        try:
            # 1. 安装基础包
            self.install_base_packages(pip_path)
            
            # 2. 安装多个扩展
            print(f"\n📦 安装 opendal[database,cloud]...")
            
            # 使用可编辑模式安装多个扩展
            install_cmd = [pip_path, "install", "-e", f"{self.base_dir}[database,cloud]"]
            result = subprocess.run(install_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"安装失败: {result.stderr}")
            
            print("✅ opendal[database,cloud] 安装成功")
            
            # 3. 验证安装的包
            print(f"\n🔍 验证安装的包:")
            list_result = subprocess.run([pip_path, "list"], capture_output=True, text=True)
            installed_list = list_result.stdout
            
            expected_packages = ['opendal', 'opendal-core', 'opendal-database', 'opendal-cloud']
            package_check = {}
            
            for pkg in expected_packages:
                found = pkg.replace('-', '_') in installed_list or pkg in installed_list
                package_check[pkg] = found
                print(f"  {pkg}: {'✅ 已安装' if found else '❌ 未安装'}")
            
            # 4. 测试来自不同扩展的服务
            print(f"\n🔧 测试来自不同扩展的服务:")
            
            mixed_services = [
                ('redis', 'database', '配置验证'),
                ('sled', 'database', '完整功能'),
                ('dropbox', 'cloud', '配置验证'),
                ('dashmap', 'cloud', '完整功能'),
                # 验证未安装的扩展仍然失败
                ('azfile', 'advanced', '应该失败')
            ]
            
            service_results = {}
            
            for service, extension_type, test_type in mixed_services:
                print(f"\n  测试 {service} (来自{extension_type}扩展, {test_type}):")
                
                test_script = f'''
import tempfile
import os

try:
    import opendal
    
    # 服务配置
    configs = {{
        "redis": {{"endpoint": "redis://localhost:6379"}},
        "sled": {{"datadir": tempfile.mkdtemp()}},
        "dropbox": {{"access_token": "test_token"}},
        "dashmap": {{}},
        "azfile": {{"endpoint": "https://test.file.core.windows.net", "share_name": "test"}}
    }}
    
    config = configs.get("{service}", {{}})
    
    op = opendal.Operator("{service}", **config)
    print("✅ Operator 创建成功")
    
    # 对于内存类服务，尝试I/O操作
    if "{service}" in ["sled", "dashmap"]:
        try:
            test_key = "scenario3_test"
            test_data = b"Multi-extension test"
            
            op.write(test_key, test_data)
            read_data = op.read(test_key)
            
            if read_data == test_data:
                print("✅ 完整I/O测试成功")
            else:
                print("❌ I/O数据不匹配")
                
        except Exception as io_e:
            print(f"⚠️ I/O测试失败: {{io_e}}")
    else:
        print("✅ 配置验证通过")

except ImportError as e:
    if "{test_type}" == "应该失败":
        print(f"✅ 预期的失败: {{e}}")
    else:
        print(f"❌ 意外的导入失败: {{e}}")
except Exception as e:
    if "{test_type}" == "应该失败":
        print(f"✅ 预期的失败: {{type(e).__name__}}: {{e}}")
    else:
        print(f"❌ 意外错误: {{type(e).__name__}}: {{e}}")
'''
                
                result = subprocess.run([python_path, "-c", test_script], 
                                      capture_output=True, text=True)
                
                output = result.stdout.strip()
                
                if test_type == "应该失败":
                    success = "预期的失败" in output
                else:
                    success = "✅" in output and result.returncode == 0
                
                service_results[service] = {
                    'extension_type': extension_type,
                    'test_type': test_type,
                    'success': success,
                    'output': output
                }
                
                if output:
                    for line in output.split('\n'):
                        if line.strip():
                            print(f"    {line}")
            
            # 5. 汇总场景3结果
            packages_installed = len([p for p in package_check.values() if p])
            services_working = len([s for s in service_results.values() if s['success']])
            
            scenario_3_result = {
                'scenario': 'multiple_optional_dependencies',
                'package_check': package_check,
                'service_results': service_results,
                'packages_success_rate': f"{packages_installed}/{len(expected_packages)}",
                'services_success_rate': f"{services_working}/{len(mixed_services)}",
                'success': packages_installed == len(expected_packages) and services_working >= len(mixed_services) * 0.8
            }
            
            self.test_results['scenario_3'] = scenario_3_result
            
            print(f"\n📊 场景3结果:")
            print(f"  包安装: {packages_installed}/{len(expected_packages)}")
            print(f"  服务功能: {services_working}/{len(mixed_services)}")
            print(f"  状态: {'✅ 通过' if scenario_3_result['success'] else '❌ 需要改进'}")
            
        except Exception as e:
            self.test_results['scenario_3'] = {
                'scenario': 'multiple_optional_dependencies',
                'error': str(e),
                'success': False
            }
            print(f"\n❌ 场景3失败: {e}")
        
        finally:
            self.cleanup_environment(temp_dir)

    def run_all_scenarios(self):
        """运行所有三个关键场景"""
        print("🚀 OpenDAL 可选依赖三大关键场景测试")
        print("="*70)
        
        # 运行三个场景
        self.scenario_1_missing_dependencies()
        self.scenario_2_single_optional_dependency()
        self.scenario_3_multiple_optional_dependencies()
        
        # 生成最终报告
        self.generate_final_report()

    def generate_final_report(self):
        """生成最终报告"""
        print(f"\n{'='*70}")
        print("📊 可选依赖三大场景测试报告")
        print("="*70)
        
        total_scenarios = len(self.test_results)
        successful_scenarios = len([r for r in self.test_results.values() if r.get('success', False)])
        
        print(f"\n📋 总体结果:")
        print(f"  测试场景: {total_scenarios}")
        print(f"  成功场景: {successful_scenarios}")
        print(f"  成功率: {successful_scenarios/total_scenarios*100:.1f}%")
        
        print(f"\n🔍 各场景详情:")
        
        scenario_names = {
            'scenario_1': '场景1: 未安装可选依赖的行为',
            'scenario_2': '场景2: 安装可选依赖的功能', 
            'scenario_3': '场景3: 多个可选依赖组合'
        }
        
        for scenario_key, result in self.test_results.items():
            scenario_name = scenario_names.get(scenario_key, scenario_key)
            status = "✅ 通过" if result.get('success', False) else "❌ 需要改进"
            print(f"\n🔸 {scenario_name}: {status}")
            
            if 'useful_error_rate' in result:
                print(f"   有用错误率: {result['useful_error_rate']}")
            if 'packages_success_rate' in result:
                print(f"   包安装率: {result['packages_success_rate']}")
            if 'services_success_rate' in result:
                print(f"   服务功能率: {result['services_success_rate']}")
            if 'error' in result:
                print(f"   错误: {result['error']}")
        
        # 关键验证点
        print(f"\n🎯 关键验证结果:")
        
        if successful_scenarios == total_scenarios:
            print("  ✅ 可选依赖机制完全正常工作")
            print("  ✅ [] 语法正确处理")
            print("  ✅ 未安装依赖时有合理错误提示")
        elif successful_scenarios >= 2:
            print("  ✅ 可选依赖机制基本正常工作")
            print("  ⚠️ 部分场景需要改进")
        else:
            print("  ❌ 可选依赖机制存在严重问题")
            print("  ❌ 需要重新检查依赖配置")
        
        # 保存详细报告
        report_file = Path("/Users/wang/i/opendal/bindings/python/tests/optional_dependency_scenarios_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return successful_scenarios >= 2


if __name__ == "__main__":
    tester = OptionalDependencyScenarios()
    success = tester.run_all_scenarios()
    
    if success:
        print("\n🎉 可选依赖场景测试基本通过！")
        sys.exit(0)
    else:
        print("\n💥 可选依赖场景测试需要改进")
        sys.exit(1)
