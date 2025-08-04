#!/usr/bin/env python3
"""
OpenDAL Python 分布式包全面测试脚本

测试所有包的服务可用性、路由正确性、体积优化等
"""

import sys
import os
import tempfile
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time

class OpenDALDistributedPackageTest:
    def __init__(self):
        self.results = {
            'core_services': {},
            'database_services': {},
            'cloud_services': {},
            'advanced_services': {},
            'routing_tests': {},
            'installation_tests': {},
            'size_tests': {}
        }
        self.temp_dir = tempfile.mkdtemp()
        print(f"📁 临时测试目录: {self.temp_dir}")

    def test_core_services(self):
        """测试核心服务包的所有服务"""
        print("\n🔧 测试核心服务 (opendal-core)")
        
        core_services = [
            ('fs', {'root': self.temp_dir}),
            ('memory', {}),
            ('http', {'endpoint': 'https://httpbin.org/'}),
            # 注意：s3, azblob 需要凭证，这里只测试配置验证
        ]
        
        for service_name, config in core_services:
            try:
                import opendal
                op = opendal.Operator(service_name, **config)
                
                # 基本功能测试
                if service_name == 'fs':
                    op.write('test.txt', b'Hello Core!')
                    content = op.read('test.txt')
                    assert content == b'Hello Core!'
                    op.delete('test.txt')
                    result = "✅ 完整功能测试通过"
                elif service_name == 'memory':
                    op.write('test.txt', b'Hello Memory!')
                    content = op.read('test.txt')
                    assert content == b'Hello Memory!'
                    result = "✅ 完整功能测试通过"
                else:
                    result = "✅ 配置验证通过"
                    
                self.results['core_services'][service_name] = result
                print(f"  {service_name}: {result}")
                
            except Exception as e:
                error_msg = f"❌ 失败: {str(e)}"
                self.results['core_services'][service_name] = error_msg
                print(f"  {service_name}: {error_msg}")

    def test_database_services(self):
        """测试数据库服务包的所有服务"""
        print("\n🗄️  测试数据库服务 (opendal-database)")
        
        database_services = [
            # 本地存储引擎 - 可以实际测试
            ('sled', {'datadir': os.path.join(self.temp_dir, 'sled')}),
            ('redb', {'datadir': os.path.join(self.temp_dir, 'redb')}),
            ('persy', {'datadir': os.path.join(self.temp_dir, 'persy')}),
            ('sqlite', {'connection_string': f'sqlite://{self.temp_dir}/test.db', 'table': 'test_table'}),
            
            # 网络服务 - 只测试配置验证
            ('redis', {'endpoint': 'redis://localhost:6379'}),
            ('mysql', {'connection_string': 'mysql://user:pass@localhost/db', 'table': 'test'}),
            ('postgresql', {'connection_string': 'postgresql://user:pass@localhost/db', 'table': 'test'}),
            ('mongodb', {'connection_string': 'mongodb://localhost:27017', 'database': 'test', 'collection': 'test'}),
            ('memcached', {'endpoint': 'memcached://localhost:11211'}),
        ]
        
        for service_name, config in database_services:
            try:
                import opendal
                op = opendal.Operator(service_name, **config)
                
                # 本地存储引擎可以做完整测试
                if service_name in ['sled', 'redb', 'persy', 'sqlite']:
                    try:
                        op.write('test_key', b'Hello Database!')
                        content = op.read('test_key')
                        assert content == b'Hello Database!'
                        result = "✅ 完整功能测试通过"
                    except Exception as write_error:
                        result = f"⚠️  创建成功但功能测试失败: {write_error}"
                else:
                    # 网络服务只验证配置
                    result = "✅ 配置验证通过"
                    
                self.results['database_services'][service_name] = result
                print(f"  {service_name}: {result}")
                
            except Exception as e:
                error_msg = f"❌ 失败: {str(e)}"
                self.results['database_services'][service_name] = error_msg
                print(f"  {service_name}: {error_msg}")

    def test_cloud_services(self):
        """测试云服务包的所有服务"""
        print("\n☁️  测试云服务 (opendal-cloud)")
        
        cloud_services = [
            # 内存/本地服务 - 可以实际测试
            ('dashmap', {}),
            ('moka', {}),
            
            # 云存储服务 - 只测试配置验证（需要凭证）
            ('dropbox', {'access_token': 'test_token'}),
            ('onedrive', {'access_token': 'test_token'}),
            ('gdrive', {'credential': 'test_credential'}),
            ('b2', {'bucket': 'test', 'application_key_id': 'test', 'application_key': 'test'}),
            ('swift', {'container': 'test', 'auth_url': 'http://test.com'}),
            ('huggingface', {'repo_id': 'test/repo'}),
            ('vercel-artifacts', {'access_token': 'test'}),
        ]
        
        for service_name, config in cloud_services:
            try:
                import opendal
                op = opendal.Operator(service_name, **config)
                
                # 内存服务可以做完整测试
                if service_name in ['dashmap', 'moka']:
                    try:
                        op.write('test_key', b'Hello Cloud!')
                        content = op.read('test_key')
                        assert content == b'Hello Cloud!'
                        result = "✅ 完整功能测试通过"
                    except Exception as write_error:
                        result = f"⚠️  创建成功但功能测试失败: {write_error}"
                else:
                    result = "✅ 配置验证通过"
                    
                self.results['cloud_services'][service_name] = result
                print(f"  {service_name}: {result}")
                
            except Exception as e:
                error_msg = f"❌ 失败: {str(e)}"
                self.results['cloud_services'][service_name] = error_msg
                print(f"  {service_name}: {error_msg}")

    def test_advanced_services(self):
        """测试高级服务包的所有服务"""
        print("\n🚀 测试高级服务 (opendal-advanced)")
        
        advanced_services = [
            # 本地缓存 - 可以实际测试
            ('mini-moka', {}),
            ('cacache', {'datadir': os.path.join(self.temp_dir, 'cacache')}),
            
            # 高级文件系统 - 只测试配置验证
            ('azfile', {'endpoint': 'https://test.file.core.windows.net', 'share_name': 'test'}),
            ('monoiofs', {'dir': self.temp_dir}),
        ]
        
        for service_name, config in advanced_services:
            try:
                import opendal
                op = opendal.Operator(service_name, **config)
                
                # 缓存服务可以做完整测试
                if service_name in ['mini-moka', 'cacache']:
                    try:
                        op.write('test_key', b'Hello Advanced!')
                        content = op.read('test_key')
                        assert content == b'Hello Advanced!'
                        result = "✅ 完整功能测试通过"
                    except Exception as write_error:
                        result = f"⚠️  创建成功但功能测试失败: {write_error}"
                else:
                    result = "✅ 配置验证通过"
                    
                self.results['advanced_services'][service_name] = result
                print(f"  {service_name}: {result}")
                
            except Exception as e:
                error_msg = f"❌ 失败: {str(e)}"
                self.results['advanced_services'][service_name] = error_msg
                print(f"  {service_name}: {error_msg}")

    def test_routing_system(self):
        """测试智能路由系统"""
        print("\n🧭 测试智能路由系统")
        
        try:
            import opendal
            
            # 测试路由映射
            routing_tests = [
                ('fs', 'opendal_core'),  # 核心服务
                ('redis', 'opendal_database'),  # 数据库服务
                ('dropbox', 'opendal_cloud'),  # 云服务
                ('azfile', 'opendal_advanced'),  # 高级服务
            ]
            
            for service, expected_package in routing_tests:
                try:
                    # 获取路由信息
                    package_name = opendal._get_service_package(service)
                    if package_name == expected_package:
                        result = f"✅ 正确路由到 {expected_package}"
                    else:
                        result = f"❌ 错误路由: 期望 {expected_package}, 实际 {package_name}"
                    
                    self.results['routing_tests'][service] = result
                    print(f"  {service} -> {result}")
                    
                except Exception as e:
                    error_msg = f"❌ 路由测试失败: {str(e)}"
                    self.results['routing_tests'][service] = error_msg
                    print(f"  {service} -> {error_msg}")
                    
        except Exception as e:
            print(f"❌ 路由系统测试失败: {e}")

    def test_api_compatibility(self):
        """测试 API 向后兼容性"""
        print("\n🔄 测试 API 向后兼容性")
        
        try:
            import opendal
            import asyncio
            
            # 测试同步 API
            op = opendal.Operator('memory')
            op.write('test', b'data')
            content = op.read('test')
            stat = op.stat('test')
            entries = list(op.list('/'))
            print("  ✅ 同步 API 完整")
            
            # 测试异步 API
            async def test_async():
                aop = opendal.AsyncOperator('memory')
                await aop.write('test', b'async_data')
                content = await aop.read('test')
                stat = await aop.stat('test')
                entries = [entry async for entry in aop.list('/')]
                return True
            
            asyncio.run(test_async())
            print("  ✅ 异步 API 完整")
            
            # 测试子模块导入
            from opendal.exceptions import NotFound, ConfigInvalid
            from opendal.layers import RetryLayer
            print("  ✅ 子模块导入正常")
            
            self.results['api_compatibility'] = "✅ 完全兼容"
            
        except Exception as e:
            error_msg = f"❌ API 兼容性测试失败: {e}"
            self.results['api_compatibility'] = error_msg
            print(f"  {error_msg}")

    def measure_package_sizes(self):
        """测量包体积"""
        print("\n📏 测量包体积")
        
        try:
            # 使用 pip show 获取包信息
            packages = ['opendal', 'opendal-core', 'opendal-database', 'opendal-cloud', 'opendal-advanced']
            
            for package in packages:
                try:
                    result = subprocess.run(['pip', 'show', package], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        # 解析输出获取位置信息
                        lines = result.stdout.split('\n')
                        location = None
                        for line in lines:
                            if line.startswith('Location:'):
                                location = line.split(':', 1)[1].strip()
                                break
                        
                        if location:
                            package_path = Path(location) / package.replace('-', '_')
                            if package_path.exists():
                                size = self._get_dir_size(package_path)
                                size_mb = size / (1024 * 1024)
                                self.results['size_tests'][package] = f"{size_mb:.2f} MB"
                                print(f"  {package}: {size_mb:.2f} MB")
                            else:
                                print(f"  {package}: 路径不存在 {package_path}")
                        else:
                            print(f"  {package}: 无法获取安装位置")
                    else:
                        print(f"  {package}: 未安装")
                        
                except Exception as e:
                    print(f"  {package}: 测量失败 - {e}")
                    
        except Exception as e:
            print(f"❌ 体积测量失败: {e}")

    def _get_dir_size(self, path: Path) -> int:
        """递归计算目录大小"""
        total_size = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception:
            pass
        return total_size

    def generate_report(self):
        """生成测试报告"""
        print("\n📊 测试报告")
        print("=" * 60)
        
        # 统计结果
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.results.items():
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    total_tests += 1
                    if "✅" in result:
                        passed_tests += 1
            elif isinstance(tests, str):
                total_tests += 1
                if "✅" in tests:
                    passed_tests += 1
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        # 详细结果
        print("\n详细结果:")
        for category, tests in self.results.items():
            print(f"\n{category.upper()}:")
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    print(f"  {test_name}: {result}")
            else:
                print(f"  {tests}")
        
        # 保存 JSON 报告
        report_file = Path('test_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 详细报告已保存到: {report_file}")

    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 OpenDAL Python 分布式包全面测试")
        print("=" * 60)
        
        start_time = time.time()
        
        # 运行各项测试
        self.test_core_services()
        self.test_database_services()
        self.test_cloud_services()
        self.test_advanced_services()
        self.test_routing_system()
        self.test_api_compatibility()
        self.measure_package_sizes()
        
        end_time = time.time()
        print(f"\n⏱️  总测试时间: {end_time - start_time:.2f} 秒")
        
        # 生成报告
        self.generate_report()
        
        # 清理
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


if __name__ == "__main__":
    tester = OpenDALDistributedPackageTest()
    tester.run_all_tests()
