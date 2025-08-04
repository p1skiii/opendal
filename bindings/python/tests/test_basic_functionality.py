#!/usr/bin/env python3
"""
基础功能验证脚本

阶段1测试：
1. 验证所有包的基本导入
2. 测试路由系统的正确性  
3. 验证各服务的基本可用性
"""

import sys
import os
import tempfile
import json
import time
from pathlib import Path
from typing import Dict, List, Any


class BasicFunctionalityTest:
    def __init__(self):
        self.results = {
            'import_tests': {},
            'routing_tests': {},
            'service_tests': {},
            'api_compatibility': {},
            'size_analysis': {}
        }
        self.temp_dir = tempfile.mkdtemp()
        print(f"📁 测试目录: {self.temp_dir}")

    def test_package_imports(self):
        """测试所有包的基本导入"""
        print("\n📦 测试包导入")
        
        packages = [
            'opendal',
            'opendal_core', 
            'opendal_database',
            'opendal_cloud',
            'opendal_advanced'
        ]
        
        for package in packages:
            try:
                # 测试基本导入
                __import__(package)
                
                # 测试关键组件导入
                if package == 'opendal':
                    from opendal import Operator, AsyncOperator
                    from opendal.exceptions import NotFound
                    from opendal.layers import RetryLayer
                    result = "✅ 完整导入成功"
                else:
                    # 子包应该包含 Operator 等基本类
                    module = __import__(package)
                    if hasattr(module, 'Operator'):
                        result = "✅ 基本组件导入成功"
                    else:
                        result = "⚠️ 导入成功但缺少基本组件"
                
                self.results['import_tests'][package] = result
                print(f"  {package}: {result}")
                
            except ImportError as e:
                error_msg = f"❌ 导入失败: {e}"
                self.results['import_tests'][package] = error_msg
                print(f"  {package}: {error_msg}")
            except Exception as e:
                error_msg = f"❌ 其他错误: {e}"
                self.results['import_tests'][package] = error_msg
                print(f"  {package}: {error_msg}")

    def test_routing_correctness(self):
        """测试路由系统的正确性"""
        print("\n🧭 测试路由系统")
        
        # 定义服务到预期包的映射
        routing_map = {
            # 核心服务
            'fs': 'opendal_core',
            'memory': 'opendal_core', 
            's3': 'opendal_core',
            'azblob': 'opendal_core',
            
            # 数据库服务
            'redis': 'opendal_database',
            'mysql': 'opendal_database',
            'postgresql': 'opendal_database',
            'sqlite': 'opendal_database',
            'mongodb': 'opendal_database',
            'sled': 'opendal_database',
            
            # 云服务
            'dropbox': 'opendal_cloud',
            'onedrive': 'opendal_cloud',
            'gdrive': 'opendal_cloud',
            'b2': 'opendal_cloud',
            'dashmap': 'opendal_cloud',
            'moka': 'opendal_cloud',
            
            # 高级服务
            'azfile': 'opendal_advanced',
            'mini-moka': 'opendal_advanced',
            'cacache': 'opendal_advanced',
        }
        
        try:
            import opendal
            
            for service, expected_package in routing_map.items():
                try:
                    # 测试路由函数
                    actual_package = opendal._get_service_package(service)
                    
                    if actual_package == expected_package:
                        result = f"✅ 正确路由到 {expected_package}"
                    else:
                        result = f"❌ 路由错误: 期望 {expected_package}, 实际 {actual_package}"
                    
                    self.results['routing_tests'][service] = result
                    print(f"  {service}: {result}")
                    
                except Exception as e:
                    error_msg = f"❌ 路由测试失败: {e}"
                    self.results['routing_tests'][service] = error_msg
                    print(f"  {service}: {error_msg}")
                    
        except ImportError as e:
            error_msg = f"❌ 无法导入 opendal: {e}"
            self.results['routing_tests']['overall'] = error_msg
            print(f"  {error_msg}")

    def test_service_availability(self):
        """测试各服务的基本可用性"""
        print("\n🔧 测试服务可用性")
        
        # 定义可以实际测试的服务
        testable_services = [
            # 核心服务 - 可以完整测试
            ('memory', {}, True),  # 内存存储
            ('fs', {'root': self.temp_dir}, True),  # 文件系统
            
            # 数据库服务 - 本地存储可以测试
            ('sled', {'datadir': os.path.join(self.temp_dir, 'sled')}, True),
            ('redb', {'datadir': os.path.join(self.temp_dir, 'redb')}, True),
            ('persy', {'datadir': os.path.join(self.temp_dir, 'persy')}, True),
            
            # 云服务 - 内存缓存可以测试
            ('dashmap', {}, True),
            ('moka', {}, True),
            
            # 高级服务 - 缓存可以测试
            ('mini-moka', {}, True),
            ('cacache', {'datadir': os.path.join(self.temp_dir, 'cacache')}, True),
            
            # 需要凭证的服务 - 只测试配置验证
            ('redis', {'endpoint': 'redis://localhost:6379'}, False),
            ('mysql', {'connection_string': 'mysql://user:pass@localhost/db', 'table': 'test'}, False),
            ('dropbox', {'access_token': 'test_token'}, False),
            ('azfile', {'endpoint': 'https://test.file.core.windows.net', 'share_name': 'test'}, False),
        ]
        
        import opendal
        
        for service_name, config, can_test_io in testable_services:
            try:
                # 测试 Operator 创建
                op = opendal.Operator(service_name, **config)
                
                if can_test_io:
                    try:
                        # 测试完整的 I/O 操作
                        test_key = f'test_key_{int(time.time())}'
                        test_data = b'Hello OpenDAL!'
                        
                        # 写入
                        op.write(test_key, test_data)
                        
                        # 读取
                        read_data = op.read(test_key)
                        assert read_data == test_data, f"数据不匹配: {read_data} != {test_data}"
                        
                        # 元数据
                        stat = op.stat(test_key)
                        assert stat.content_length == len(test_data), f"大小不匹配: {stat.content_length} != {len(test_data)}"
                        
                        # 清理
                        try:
                            op.delete(test_key)
                        except:
                            pass  # 某些服务可能不支持删除
                        
                        result = "✅ 完整功能测试通过"
                        
                    except Exception as io_error:
                        result = f"⚠️ 创建成功但 I/O 测试失败: {io_error}"
                else:
                    # 只验证配置（会在后续操作中报错，但这是预期的）
                    result = "✅ 配置验证通过"
                
                self.results['service_tests'][service_name] = result
                print(f"  {service_name}: {result}")
                
            except Exception as e:
                error_msg = f"❌ 失败: {str(e)[:100]}..."
                self.results['service_tests'][service_name] = error_msg
                print(f"  {service_name}: {error_msg}")

    def test_api_compatibility(self):
        """测试 API 向后兼容性"""
        print("\n🔄 测试 API 兼容性")
        
        try:
            import opendal
            import asyncio
            
            compatibility_tests = {}
            
            # 测试同步 API
            try:
                op = opendal.Operator('memory')
                
                # 基本操作
                op.write('test', b'data')
                content = op.read('test')
                stat = op.stat('test')
                entries = list(op.list('/'))
                
                # 高级操作
                with op.writer('test2') as writer:
                    writer.write(b'writer_data')
                
                with op.reader('test') as reader:
                    reader_data = reader.read()
                
                compatibility_tests['sync_api'] = "✅ 同步 API 完整"
                
            except Exception as e:
                compatibility_tests['sync_api'] = f"❌ 同步 API 失败: {e}"
            
            # 测试异步 API
            try:
                async def test_async():
                    aop = opendal.AsyncOperator('memory')
                    
                    # 基本操作
                    await aop.write('async_test', b'async_data')
                    content = await aop.read('async_test')
                    stat = await aop.stat('async_test')
                    entries = [entry async for entry in aop.list('/')]
                    
                    # 高级操作
                    async with aop.writer('async_test2') as writer:
                        await writer.write(b'async_writer_data')
                    
                    async with aop.reader('async_test') as reader:
                        reader_data = await reader.read()
                    
                    return True
                
                asyncio.run(test_async())
                compatibility_tests['async_api'] = "✅ 异步 API 完整"
                
            except Exception as e:
                compatibility_tests['async_api'] = f"❌ 异步 API 失败: {e}"
            
            # 测试子模块导入
            try:
                from opendal.exceptions import NotFound, ConfigInvalid, PermissionDenied
                from opendal.layers import RetryLayer, ConcurrentLimitLayer
                compatibility_tests['submodules'] = "✅ 子模块导入正常"
                
            except Exception as e:
                compatibility_tests['submodules'] = f"❌ 子模块导入失败: {e}"
            
            # 测试类型和属性
            try:
                op = opendal.Operator('memory')
                
                # 测试 capability
                cap = op.capability()
                assert hasattr(cap, 'read'), "缺少 read capability"
                assert hasattr(cap, 'write'), "缺少 write capability"
                
                # 测试 metadata
                op.write('meta_test', b'test')
                meta = op.stat('meta_test')
                assert hasattr(meta, 'content_length'), "缺少 content_length"
                assert hasattr(meta, 'last_modified'), "缺少 last_modified"
                
                compatibility_tests['types_attributes'] = "✅ 类型和属性完整"
                
            except Exception as e:
                compatibility_tests['types_attributes'] = f"❌ 类型测试失败: {e}"
            
            self.results['api_compatibility'] = compatibility_tests
            
            # 打印结果
            for test_name, result in compatibility_tests.items():
                print(f"  {test_name}: {result}")
                
        except ImportError as e:
            error_msg = f"❌ 无法导入 opendal: {e}"
            self.results['api_compatibility']['import_error'] = error_msg
            print(f"  {error_msg}")

    def analyze_package_sizes(self):
        """分析包大小"""
        print("\n📏 分析包大小")
        
        try:
            import pkg_resources
            import site
            
            # 获取 site-packages 路径
            site_packages_paths = site.getsitepackages()
            if not site_packages_paths:
                site_packages_paths = [site.getusersitepackages()]
            
            size_info = {}
            total_size = 0
            
            packages = ['opendal', 'opendal_core', 'opendal_database', 'opendal_cloud', 'opendal_advanced']
            
            for package in packages:
                try:
                    # 尝试获取包信息
                    dist = pkg_resources.get_distribution(package.replace('_', '-'))
                    
                    # 查找包目录
                    package_path = None
                    for sp_path in site_packages_paths:
                        potential_path = Path(sp_path) / package
                        if potential_path.exists():
                            package_path = potential_path
                            break
                    
                    if package_path:
                        size = self._calculate_directory_size(package_path)
                        size_mb = size / (1024 * 1024)
                        size_info[package] = {
                            'size_bytes': size,
                            'size_mb': f"{size_mb:.2f} MB",
                            'version': dist.version
                        }
                        total_size += size
                        print(f"  {package}: {size_mb:.2f} MB")
                    else:
                        size_info[package] = {'error': '路径未找到'}
                        print(f"  {package}: 路径未找到")
                        
                except pkg_resources.DistributionNotFound:
                    size_info[package] = {'error': '包未安装'}
                    print(f"  {package}: 包未安装")
                except Exception as e:
                    size_info[package] = {'error': str(e)}
                    print(f"  {package}: 错误 - {e}")
            
            # 计算总大小
            total_mb = total_size / (1024 * 1024)
            size_info['total'] = {
                'size_bytes': total_size,
                'size_mb': f"{total_mb:.2f} MB"
            }
            
            print(f"\n📊 总安装大小: {total_mb:.2f} MB")
            
            self.results['size_analysis'] = size_info
            
        except Exception as e:
            error_msg = f"❌ 大小分析失败: {e}"
            self.results['size_analysis'] = {'error': error_msg}
            print(f"  {error_msg}")

    def _calculate_directory_size(self, path: Path) -> int:
        """递归计算目录大小"""
        total_size = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, IOError):
                        # 忽略无法访问的文件
                        pass
        except Exception:
            pass
        return total_size

    def generate_summary_report(self):
        """生成测试摘要报告"""
        print(f"\n{'='*60}")
        print("📊 基础功能验证报告")
        print("="*60)
        
        # 统计各类测试结果
        categories = ['import_tests', 'routing_tests', 'service_tests']
        
        for category in categories:
            if category in self.results:
                tests = self.results[category]
                if isinstance(tests, dict):
                    total = len(tests)
                    passed = len([t for t in tests.values() if '✅' in str(t)])
                    print(f"\n{category.replace('_', ' ').title()}:")
                    print(f"  通过: {passed}/{total} ({passed/total*100:.1f}%)")
                    
                    # 显示失败的测试
                    failed = [(k, v) for k, v in tests.items() if '❌' in str(v)]
                    if failed:
                        print("  失败项:")
                        for name, error in failed[:3]:  # 只显示前3个
                            print(f"    {name}: {str(error)[:50]}...")
        
        # API 兼容性
        if 'api_compatibility' in self.results:
            api_tests = self.results['api_compatibility']
            if isinstance(api_tests, dict):
                api_total = len(api_tests)
                api_passed = len([t for t in api_tests.values() if '✅' in str(t)])
                print(f"\nAPI 兼容性:")
                print(f"  通过: {api_passed}/{api_total} ({api_passed/api_total*100:.1f}%)")
        
        # 大小信息
        if 'size_analysis' in self.results and 'total' in self.results['size_analysis']:
            total_size = self.results['size_analysis']['total']
            if 'size_mb' in total_size:
                print(f"\n安装大小: {total_size['size_mb']}")
        
        # 保存详细报告
        report_file = Path("/Users/wang/i/opendal/bindings/python/tests/basic_functionality_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")

    def run_all_tests(self):
        """运行所有基础功能测试"""
        print("🧪 OpenDAL 基础功能验证测试")
        print("="*60)
        
        start_time = time.time()
        
        # 运行各项测试
        self.test_package_imports()
        self.test_routing_correctness()
        self.test_service_availability()
        self.test_api_compatibility()
        self.analyze_package_sizes()
        
        end_time = time.time()
        print(f"\n⏱️ 总测试时间: {end_time - start_time:.2f} 秒")
        
        # 生成报告
        self.generate_summary_report()
        
        # 清理
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    tester = BasicFunctionalityTest()
    tester.run_all_tests()
