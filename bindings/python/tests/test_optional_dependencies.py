#!/usr/bin/env python3
"""
可选依赖测试脚本

测试 pip install opendal[database] 等按需安装功能
"""

import subprocess
import sys
import tempfile
import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Tuple


class OptionalDependencyTest:
    def __init__(self):
        self.test_results = {}
        self.original_dir = os.getcwd()
        
    def create_test_environment(self, env_name: str):
        """创建测试环境"""
        print(f"\n🐍 创建测试环境: {env_name}")
        
        temp_dir = tempfile.mkdtemp(prefix=f"opendal_optional_{env_name}_")
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
        
        print(f"📁 环境目录: {temp_dir}")
        return temp_dir, python_path, pip_path

    def cleanup_environment(self, temp_dir: str):
        """清理测试环境"""
        os.chdir(self.original_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def setup_local_package_index(self, pip_path: str):
        """设置本地包索引（模拟 PyPI）"""
        print("📦 设置本地包...")
        
        # 安装所有本地构建的包
        wheels = [
            "/Users/wang/i/opendal/bindings/python/packages/opendal-core/dist/opendal_core-0.46.0-cp311-cp311-macosx_11_0_arm64.whl",
            "/Users/wang/i/opendal/bindings/python/packages/opendal-database/dist/opendal_database-0.46.0-cp311-cp311-macosx_11_0_arm64.whl",
            "/Users/wang/i/opendal/bindings/python/packages/opendal-cloud/dist/opendal_cloud-0.46.0-cp311-cp311-macosx_11_0_arm64.whl",
            "/Users/wang/i/opendal/bindings/python/packages/opendal-advanced/dist/opendal_advanced-0.46.0-cp311-cp311-macosx_11_0_arm64.whl"
        ]
        
        for wheel in wheels:
            if Path(wheel).exists():
                result = subprocess.run([pip_path, "install", wheel], capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"安装失败 {wheel}: {result.stderr}")
                print(f"  ✅ 已安装: {Path(wheel).name}")
            else:
                raise Exception(f"Wheel 文件不存在: {wheel}")

    def test_installation_scenario(self, scenario_name: str, install_options: str, expected_packages: List[str], test_services: List[Tuple[str, str]]):
        """测试一个安装场景"""
        print(f"\n{'='*70}")
        print(f"🧪 测试场景: {scenario_name}")
        print(f"📦 安装选项: opendal{install_options}")
        
        temp_dir, python_path, pip_path = self.create_test_environment(scenario_name.replace(' ', '_'))
        
        try:
            # 1. 设置本地包
            self.setup_local_package_index(pip_path)
            
            # 2. 重新构建元包并安装
            print(f"\n📥 安装元包: opendal{install_options}")
            
            # 先构建最新的元包
            build_dir = "/Users/wang/i/opendal/bindings/python"
            build_result = subprocess.run(["uv", "build", ".", "--wheel"], 
                                        cwd=build_dir, capture_output=True, text=True)
            if build_result.returncode != 0:
                raise Exception(f"构建元包失败: {build_result.stderr}")
            
            # 找到最新构建的元包
            dist_dir = Path(build_dir) / "dist"
            meta_wheels = list(dist_dir.glob("opendal-*.whl"))
            if not meta_wheels:
                raise Exception("未找到元包 wheel")
            
            latest_meta_wheel = max(meta_wheels, key=lambda p: p.stat().st_mtime)
            print(f"📦 使用元包: {latest_meta_wheel.name}")
            
            # 安装元包（使用可选依赖）
            if install_options:
                install_cmd = [pip_path, "install", f"{latest_meta_wheel}{install_options}"]
            else:
                install_cmd = [pip_path, "install", str(latest_meta_wheel)]
            
            result = subprocess.run(install_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"元包安装失败: {result.stderr}")
            
            print("✅ 元包安装成功")
            
            # 3. 验证已安装的包
            print(f"\n🔍 验证安装的包...")
            list_result = subprocess.run([pip_path, "list"], capture_output=True, text=True)
            installed_packages = list_result.stdout
            
            package_check = {}
            for expected_pkg in expected_packages:
                if expected_pkg.replace('_', '-') in installed_packages:
                    package_check[expected_pkg] = "✅ 已安装"
                    print(f"  {expected_pkg}: ✅ 已安装")
                else:
                    package_check[expected_pkg] = "❌ 未安装"
                    print(f"  {expected_pkg}: ❌ 未安装")
            
            # 4. 测试服务可用性
            print(f"\n🔧 测试服务可用性...")
            service_results = {}
            
            for service_name, expected_result in test_services:
                print(f"\n  测试服务: {service_name}")
                
                test_script = f'''
import sys
import tempfile
import os

try:
    import opendal
    
    # 基本配置
    if "{service_name}" == "memory":
        config = {{}}
    elif "{service_name}" == "fs":
        config = {{"root": tempfile.gettempdir()}}
    elif "{service_name}" == "redis":
        config = {{"endpoint": "redis://localhost:6379"}}
    elif "{service_name}" == "sqlite":
        config = {{"connection_string": "sqlite:///test.db", "table": "test_table"}}
    elif "{service_name}" == "dropbox":
        config = {{"access_token": "test_token"}}
    elif "{service_name}" == "dashmap":
        config = {{}}
    elif "{service_name}" == "azfile":
        config = {{"endpoint": "https://test.file.core.windows.net", "share_name": "test"}}
    elif "{service_name}" == "cacache":
        config = {{"datadir": tempfile.mkdtemp()}}
    else:
        config = {{}}
    
    # 尝试创建 Operator
    op = opendal.Operator("{service_name}", **config)
    print("✅ 服务可用")
    
    # 对于可以完整测试的服务，进行 I/O 测试
    if "{service_name}" in ["memory", "fs", "dashmap"]:
        try:
            op.write("test_key", b"test_data")
            data = op.read("test_key")
            if data == b"test_data":
                print("✅ I/O 测试成功")
            else:
                print("⚠️ I/O 测试数据不匹配")
        except Exception as io_e:
            print(f"⚠️ I/O 测试失败: {{io_e}}")

except ImportError as e:
    if "{expected_result}" == "should_fail":
        print(f"✅ 预期的导入失败: {{e}}")
    else:
        print(f"❌ 意外的导入失败: {{e}}")
except Exception as e:
    if "{expected_result}" == "should_fail":
        print(f"✅ 预期的错误: {{type(e).__name__}}: {{e}}")
    else:
        print(f"❌ 意外错误: {{type(e).__name__}}: {{e}}")
'''
                
                result = subprocess.run([python_path, "-c", test_script], 
                                      capture_output=True, text=True)
                
                service_output = result.stdout.strip()
                service_success = "✅" in service_output
                
                service_results[service_name] = {
                    'expected': expected_result,
                    'success': service_success,
                    'output': service_output
                }
                
                # 打印结果
                if expected_result == "should_work" and service_success:
                    print(f"    ✅ 按预期工作")
                elif expected_result == "should_fail" and "预期" in service_output:
                    print(f"    ✅ 按预期失败")
                else:
                    print(f"    ⚠️ 意外结果")
                
                if service_output:
                    for line in service_output.split('\n'):
                        if line.strip():
                            print(f"      {line}")
            
            # 5. 汇总结果
            total_packages = len(expected_packages)
            installed_count = len([p for p in package_check.values() if "✅" in p])
            
            total_services = len(test_services)
            working_services = len([s for s in service_results.values() if s['success']])
            
            scenario_result = {
                'scenario_name': scenario_name,
                'install_options': install_options,
                'package_check': package_check,
                'package_success_rate': f"{installed_count}/{total_packages}",
                'service_results': service_results,
                'service_success_rate': f"{working_services}/{total_services}",
                'overall_success': installed_count == total_packages and working_services >= total_services * 0.8
            }
            
            self.test_results[scenario_name] = scenario_result
            
            print(f"\n📊 {scenario_name} 结果摘要:")
            print(f"  包安装率: {installed_count}/{total_packages}")
            print(f"  服务可用率: {working_services}/{total_services}")
            print(f"  整体状态: {'✅ 通过' if scenario_result['overall_success'] else '❌ 失败'}")
            
        except Exception as e:
            error_result = {
                'scenario_name': scenario_name,
                'install_options': install_options,
                'error': str(e),
                'overall_success': False
            }
            self.test_results[scenario_name] = error_result
            print(f"\n❌ {scenario_name} 测试失败: {e}")
        
        finally:
            self.cleanup_environment(temp_dir)

    def run_all_optional_dependency_tests(self):
        """运行所有可选依赖测试"""
        print("🚀 OpenDAL 可选依赖测试")
        print("="*70)
        print("目标: 验证 pip install opendal[x] 按需安装功能")
        
        # 定义测试场景
        scenarios = [
            {
                'name': '仅核心包',
                'options': '',  # pip install opendal
                'expected_packages': ['opendal', 'opendal_core'],
                'test_services': [
                    ('memory', 'should_work'),
                    ('fs', 'should_work'),
                    ('redis', 'should_fail'),  # 数据库服务应该失败
                ]
            },
            {
                'name': '数据库扩展',
                'options': '[database]',  # pip install opendal[database]
                'expected_packages': ['opendal', 'opendal_core', 'opendal_database'],
                'test_services': [
                    ('memory', 'should_work'),
                    ('redis', 'should_work'),
                    ('sqlite', 'should_work'),
                    ('dropbox', 'should_fail'),  # 云服务应该失败
                ]
            },
            {
                'name': '云服务扩展',
                'options': '[cloud]',  # pip install opendal[cloud]
                'expected_packages': ['opendal', 'opendal_core', 'opendal_cloud'],
                'test_services': [
                    ('memory', 'should_work'),
                    ('dashmap', 'should_work'),
                    ('dropbox', 'should_work'),
                    ('redis', 'should_fail'),  # 数据库服务应该失败
                ]
            },
            {
                'name': '高级服务扩展',
                'options': '[advanced]',  # pip install opendal[advanced]
                'expected_packages': ['opendal', 'opendal_core', 'opendal_advanced'],
                'test_services': [
                    ('memory', 'should_work'),
                    ('cacache', 'should_work'),
                    ('azfile', 'should_work'),
                    ('redis', 'should_fail'),  # 数据库服务应该失败
                ]
            },
            {
                'name': '全部服务',
                'options': '[all]',  # pip install opendal[all]
                'expected_packages': ['opendal', 'opendal_core', 'opendal_database', 'opendal_cloud', 'opendal_advanced'],
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
                scenario['options'],
                scenario['expected_packages'],
                scenario['test_services']
            )
        
        # 生成最终报告
        self.generate_final_report()

    def generate_final_report(self):
        """生成最终报告"""
        print(f"\n{'='*70}")
        print("📊 可选依赖测试报告")
        print("="*70)
        
        total_scenarios = len(self.test_results)
        successful_scenarios = len([r for r in self.test_results.values() if r.get('overall_success', False)])
        
        print(f"\n📋 总体结果:")
        print(f"  测试场景: {total_scenarios}")
        print(f"  成功场景: {successful_scenarios}")
        print(f"  成功率: {successful_scenarios/total_scenarios*100:.1f}%")
        
        print(f"\n🔍 各场景详情:")
        for scenario_name, result in self.test_results.items():
            status = "✅ 通过" if result.get('overall_success', False) else "❌ 失败"
            print(f"\n🔸 {scenario_name}: {status}")
            
            if 'package_success_rate' in result:
                print(f"   包安装: {result['package_success_rate']}")
            
            if 'service_success_rate' in result:
                print(f"   服务可用: {result['service_success_rate']}")
            
            if 'error' in result:
                print(f"   错误: {result['error']}")
        
        # 关键结论
        print(f"\n🎯 关键结论:")
        if successful_scenarios == total_scenarios:
            print("  ✅ 按需安装功能完全正常")
            print("  ✅ 所有 opendal[x] 选项都正确工作")
        elif successful_scenarios > 0:
            print(f"  ⚠️ 部分按需安装功能正常 ({successful_scenarios}/{total_scenarios})")
            print("  ⚠️ 需要修复部分可选依赖")
        else:
            print("  ❌ 按需安装功能存在严重问题")
            print("  ❌ 需要重新检查依赖配置")
        
        # 保存详细报告
        report_file = Path("/Users/wang/i/opendal/bindings/python/tests/optional_dependency_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return successful_scenarios == total_scenarios


if __name__ == "__main__":
    tester = OptionalDependencyTest()
    success = tester.run_all_optional_dependency_tests()
    
    if success:
        print("\n🎉 所有可选依赖测试通过！")
        sys.exit(0)
    else:
        print("\n💥 可选依赖测试存在问题，需要修复")
        sys.exit(1)
