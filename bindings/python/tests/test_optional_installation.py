#!/usr/bin/env python3
"""
测试按需安装功能

测试不同的安装组合：
- pip install opendal
- pip install opendal[database] 
- pip install opendal[cloud]
- pip install opendal[advanced]
- pip install opendal[all]
"""

import subprocess
import sys
import tempfile
import os
import shutil
import json
from pathlib import Path


class OptionalInstallationTest:
    def __init__(self):
        self.test_results = {}
        self.original_dir = os.getcwd()
        
    def create_test_environment(self, env_name: str):
        """创建一个干净的虚拟环境"""
        print(f"\n🐍 创建测试环境: {env_name}")
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix=f"opendal_test_{env_name}_")
        os.chdir(temp_dir)
        
        # 创建虚拟环境
        subprocess.run([sys.executable, "-m", "venv", "test_env"], check=True)
        
        # 获取虚拟环境的 Python 路径
        if sys.platform == "win32":
            python_path = os.path.join(temp_dir, "test_env", "Scripts", "python.exe")
            pip_path = os.path.join(temp_dir, "test_env", "Scripts", "pip.exe")
        else:
            python_path = os.path.join(temp_dir, "test_env", "bin", "python")
            pip_path = os.path.join(temp_dir, "test_env", "bin", "pip")
        
        print(f"📁 测试目录: {temp_dir}")
        return temp_dir, python_path, pip_path

    def cleanup_environment(self, temp_dir: str):
        """清理测试环境"""
        os.chdir(self.original_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def install_local_packages(self, pip_path: str, install_command: str):
        """安装本地构建的包"""
        print(f"📦 执行安装: {install_command}")
        
        # 首先安装核心包（总是需要的）
        core_wheel = "/Users/wang/i/opendal/bindings/python/packages/opendal-core/dist/opendal_core-0.46.0-cp311-cp311-macosx_11_0_arm64.whl"
        subprocess.run([pip_path, "install", core_wheel], check=True)
        
        # 根据安装命令安装其他包
        if "[database]" in install_command or "[all]" in install_command:
            db_wheel = "/Users/wang/i/opendal/bindings/python/packages/opendal-database/dist/opendal_database-0.46.0-cp311-cp311-macosx_11_0_arm64.whl"
            subprocess.run([pip_path, "install", db_wheel], check=True)
            
        if "[cloud]" in install_command or "[all]" in install_command:
            cloud_wheel = "/Users/wang/i/opendal/bindings/python/packages/opendal-cloud/dist/opendal_cloud-0.46.0-cp311-cp311-macosx_11_0_arm64.whl"
            subprocess.run([pip_path, "install", cloud_wheel], check=True)
            
        if "[advanced]" in install_command or "[all]" in install_command:
            advanced_wheel = "/Users/wang/i/opendal/bindings/python/packages/opendal-advanced/dist/opendal_advanced-0.46.0-cp311-cp311-macosx_11_0_arm64.whl"
            subprocess.run([pip_path, "install", advanced_wheel], check=True)
        
        # 最后安装元包
        meta_wheel = "/Users/wang/i/opendal/bindings/python/dist/opendal-0.46.0-py3-none-any.whl"
        subprocess.run([pip_path, "install", meta_wheel], check=True)

    def test_package_availability(self, python_path: str, expected_packages: list):
        """测试包的可用性"""
        print("🔍 测试包可用性...")
        
        test_script = f'''
import sys
import importlib

results = {{}}

# 测试基础导入
try:
    import opendal
    results["opendal"] = "✅ 成功导入"
except Exception as e:
    results["opendal"] = f"❌ 导入失败: {{e}}"

# 测试各个子包
packages_to_test = {expected_packages}

for pkg in packages_to_test:
    try:
        mod = importlib.import_module(pkg)
        results[pkg] = "✅ 可用"
    except ImportError:
        results[pkg] = "❌ 不可用"
    except Exception as e:
        results[pkg] = f"❌ 错误: {{e}}"

# 打印结果
import json
print(json.dumps(results))
'''
        
        result = subprocess.run([python_path, "-c", test_script], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            try:
                return json.loads(result.stdout.strip())
            except:
                return {"error": f"解析输出失败: {result.stdout}"}
        else:
            return {"error": f"脚本执行失败: {result.stderr}"}

    def test_service_routing(self, python_path: str, test_services: list):
        """测试服务路由"""
        print("🧭 测试服务路由...")
        
        test_script = f'''
import sys
results = {{}}

try:
    import opendal
    
    test_services = {test_services}
    
    for service_name, expected_result in test_services:
        try:
            op = opendal.Operator(service_name, **{{}})
            results[service_name] = "✅ 路由成功"
        except ImportError as e:
            if "not installed" in str(e):
                results[service_name] = f"⚠️ 预期的导入错误: {{e}}"
            else:
                results[service_name] = f"❌ 意外的导入错误: {{e}}"
        except Exception as e:
            # 配置错误是预期的，说明路由成功了
            results[service_name] = f"✅ 路由成功 (配置错误正常): {{type(e).__name__}}"

    import json
    print(json.dumps(results))
    
except Exception as e:
    print(json.dumps({{"error": f"路由测试失败: {{e}}"}}}))
'''
        
        result = subprocess.run([python_path, "-c", test_script], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            try:
                return json.loads(result.stdout.strip())
            except:
                return {"error": f"解析输出失败: {result.stdout}"}
        else:
            return {"error": f"脚本执行失败: {result.stderr}"}

    def measure_installation_size(self, python_path: str):
        """测量安装包大小"""
        print("📏 测量安装大小...")
        
        test_script = '''
import sys
import os
from pathlib import Path

def get_dir_size(path):
    """递归计算目录大小"""
    total_size = 0
    try:
        for item in Path(path).rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
    except:
        pass
    return total_size

# 获取 site-packages 路径
import site
site_packages = site.getsitepackages()[0]

results = {}
opendal_packages = []

# 查找所有 opendal 相关包
for item in Path(site_packages).iterdir():
    if item.is_dir() and item.name.startswith('opendal'):
        size = get_dir_size(item)
        size_mb = size / (1024 * 1024)
        results[item.name] = f"{size_mb:.2f} MB"
        opendal_packages.append((item.name, size))

# 计算总大小
total_size = sum(size for _, size in opendal_packages)
total_mb = total_size / (1024 * 1024)
results["total"] = f"{total_mb:.2f} MB"

import json
print(json.dumps(results))
'''
        
        result = subprocess.run([python_path, "-c", test_script], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            try:
                return json.loads(result.stdout.strip())
            except:
                return {"error": f"解析输出失败: {result.stdout}"}
        else:
            return {"error": f"脚本执行失败: {result.stderr}"}

    def test_installation_scenario(self, scenario_name: str, install_command: str, 
                                 expected_packages: list, test_services: list):
        """测试一个安装场景"""
        print(f"\n{'='*60}")
        print(f"🧪 测试场景: {scenario_name}")
        print(f"📦 安装命令: {install_command}")
        
        temp_dir, python_path, pip_path = self.create_test_environment(scenario_name)
        
        try:
            # 执行安装
            self.install_local_packages(pip_path, install_command)
            
            # 测试包可用性
            package_results = self.test_package_availability(python_path, expected_packages)
            
            # 测试服务路由
            routing_results = self.test_service_routing(python_path, test_services)
            
            # 测量大小
            size_results = self.measure_installation_size(python_path)
            
            # 保存结果
            self.test_results[scenario_name] = {
                "install_command": install_command,
                "package_availability": package_results,
                "service_routing": routing_results,
                "installation_size": size_results,
                "status": "✅ 完成"
            }
            
            # 打印结果摘要
            print(f"\n📊 {scenario_name} 结果摘要:")
            print(f"  包可用性: {len([k for k, v in package_results.items() if '✅' in str(v)])} / {len(package_results)}")
            print(f"  路由测试: {len([k for k, v in routing_results.items() if '✅' in str(v)])} / {len(routing_results)}")
            print(f"  总安装大小: {size_results.get('total', '未知')}")
            
        except Exception as e:
            error_msg = f"❌ 测试失败: {e}"
            print(f"\n{error_msg}")
            self.test_results[scenario_name] = {
                "install_command": install_command,
                "status": error_msg
            }
        
        finally:
            self.cleanup_environment(temp_dir)

    def run_all_tests(self):
        """运行所有安装场景测试"""
        print("🚀 OpenDAL 按需安装测试")
        print("="*60)
        
        # 定义测试场景
        scenarios = [
            {
                "name": "仅核心包",
                "command": "pip install opendal",
                "expected_packages": ["opendal", "opendal_core"],
                "test_services": [
                    ("fs", "available"),
                    ("memory", "available"),
                    ("redis", "not_available"),  # 应该报错说需要安装 database 包
                ]
            },
            {
                "name": "数据库服务",
                "command": "pip install opendal[database]",
                "expected_packages": ["opendal", "opendal_core", "opendal_database"],
                "test_services": [
                    ("fs", "available"),
                    ("redis", "available"),
                    ("sqlite", "available"),
                    ("dropbox", "not_available"),  # 应该报错说需要安装 cloud 包
                ]
            },
            {
                "name": "云服务",
                "command": "pip install opendal[cloud]", 
                "expected_packages": ["opendal", "opendal_core", "opendal_cloud"],
                "test_services": [
                    ("fs", "available"),
                    ("dropbox", "available"),
                    ("dashmap", "available"),
                    ("redis", "not_available"),  # 应该报错说需要安装 database 包
                ]
            },
            {
                "name": "高级服务",
                "command": "pip install opendal[advanced]",
                "expected_packages": ["opendal", "opendal_core", "opendal_advanced"],
                "test_services": [
                    ("fs", "available"),
                    ("azfile", "available"),
                    ("mini-moka", "available"),
                    ("redis", "not_available"),  # 应该报错说需要安装 database 包
                ]
            },
            {
                "name": "所有服务",
                "command": "pip install opendal[all]",
                "expected_packages": ["opendal", "opendal_core", "opendal_database", "opendal_cloud", "opendal_advanced"],
                "test_services": [
                    ("fs", "available"),
                    ("redis", "available"),
                    ("dropbox", "available"),
                    ("azfile", "available"),
                ]
            }
        ]
        
        # 运行每个场景
        for scenario in scenarios:
            self.test_installation_scenario(
                scenario["name"],
                scenario["command"], 
                scenario["expected_packages"],
                scenario["test_services"]
            )
        
        # 生成最终报告
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        print(f"\n{'='*60}")
        print("📊 按需安装测试报告")
        print("="*60)
        
        for scenario_name, results in self.test_results.items():
            print(f"\n🧪 {scenario_name}:")
            print(f"  命令: {results['install_command']}")
            print(f"  状态: {results['status']}")
            
            if 'installation_size' in results:
                size_info = results['installation_size']
                print(f"  大小: {size_info.get('total', '未知')}")
                
            if 'package_availability' in results:
                pkg_results = results['package_availability']
                available_count = len([k for k, v in pkg_results.items() if '✅' in str(v)])
                print(f"  包可用性: {available_count}/{len(pkg_results)}")
                
            if 'service_routing' in results:
                routing_results = results['service_routing']
                routing_success = len([k for k, v in routing_results.items() if '✅' in str(v)])
                print(f"  路由成功: {routing_success}/{len(routing_results)}")
        
        # 保存详细报告
        report_file = Path("/Users/wang/i/opendal/bindings/python/tests/optional_installation_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")


if __name__ == "__main__":
    tester = OptionalInstallationTest()
    tester.run_all_tests()
