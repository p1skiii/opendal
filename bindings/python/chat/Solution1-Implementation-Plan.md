# OpenDAL Python Bindings - 方案1实施方案

## 当前状态分析

### 现有结构
```
bindings/python/
├── Cargo.toml                 # 单包配置，features=services-all
├── pyproject.toml            # maturin配置，module-name="opendal._opendal"
├── src/lib.rs                # 单一绑定入口
├── python/opendal/           # Python包代码
└── 当前问题：一个50MB的大包
```

### 现有features
- `services-all`: 包含所有50+服务
- 用户无法选择性安装

---

## 目标设计

### 包分类策略
```
opendal-core      (10MB)  - 15个核心服务
opendal-database  (15MB)  - core + 数据库服务 
opendal-cloud     (20MB)  - core + 云服务
opendal-advanced  (25MB)  - core + 高级服务
opendal           (50MB)  - 完整包（向后兼容）
```

### 服务分类
```toml
# Core Services (15个基础服务)
core_services = [
    "services-azblob", "services-azdls", "services-cos", "services-fs", 
    "services-gcs", "services-ghac", "services-http", "services-ipmfs",
    "services-memory", "services-obs", "services-oss", "services-s3", 
    "services-webdav", "services-webhdfs", "services-native"
]

# Database Services
database_services = [
    "services-redis", "services-rocksdb", "services-sled", 
    "services-postgresql", "services-mysql", "services-sqlite"
]

# Cloud Services  
cloud_services = [
    "services-dropbox", "services-gdrive", "services-onedrive",
    "services-box", "services-pcloud", "services-yandex-disk"
]

# Advanced Services
advanced_services = [
    "services-tikv", "services-foundationdb", "services-etcd",
    "services-consul", "services-minio", "services-seafile"
]
```

---

## 实施步骤

### Step 1: 备份当前配置
```bash
cd /Users/wang/i/opendal/bindings/python
cp Cargo.toml Cargo.toml.backup
cp pyproject.toml pyproject.toml.backup
```

### Step 2: 重构Cargo.toml
创建新的features结构：

```toml
# 新的 Cargo.toml
[package]
name = "opendal-python"
version = "0.46.0"
edition = "2021"
publish = false
authors = ["Apache OpenDAL <dev@opendal.apache.org>"]
license = "Apache-2.0"
homepage = "https://opendal.apache.org/"
repository = "https://github.com/apache/opendal"
rust-version = "1.82"

[lib]
crate-type = ["cdylib"]
doc = false
name = "opendal"

[features]
default = ["services-core"]

# 包变体features
services-core = [
    "services-azblob", "services-azdls", "services-cos", "services-fs",
    "services-gcs", "services-ghac", "services-http", "services-ipmfs", 
    "services-memory", "services-obs", "services-oss", "services-s3",
    "services-webdav", "services-webhdfs"
]

services-database = [
    "services-core",
    "services-redis", "services-rocksdb", "services-sled",
    "services-postgresql", "services-mysql", "services-sqlite"
]

services-cloud = [
    "services-core", 
    "services-dropbox", "services-gdrive", "services-onedrive",
    "services-box", "services-pcloud"
]

services-advanced = [
    "services-core",
    "services-tikv", "services-foundationdb", "services-etcd",
    "services-consul", "services-minio"
]

services-all = [
    "services-core", "services-database", "services-cloud", "services-advanced"
]

# 单个服务features（继承原有配置）
services-azblob = ["opendal/services-azblob"]
services-azdls = ["opendal/services-azdls"]
# ... 其他所有服务的feature定义
```

### Step 3: 创建多包构建配置
创建 `build-variants.toml`:

```toml
# build-variants.toml - 构建变体配置
[[variants]]
name = "opendal-core"
features = ["services-core"]
description = "Core storage services (fs, s3, azure, gcs, etc.)"

[[variants]]  
name = "opendal-database"
features = ["services-database"]
description = "Core + Database services (redis, mysql, postgresql, etc.)"

[[variants]]
name = "opendal-cloud" 
features = ["services-cloud"]
description = "Core + Cloud services (dropbox, gdrive, onedrive, etc.)"

[[variants]]
name = "opendal-advanced"
features = ["services-advanced"]
description = "Core + Advanced services (tikv, foundationdb, etc.)"

[[variants]]
name = "opendal"
features = ["services-all"] 
description = "Complete package with all services"
```

### Step 4: 创建构建脚本
创建 `scripts/build-variants.py`:

```python
#!/usr/bin/env python3
"""Build script for different package variants"""

import subprocess
import sys
import toml
from pathlib import Path

def build_variant(name: str, features: list, description: str):
    """Build a specific package variant"""
    print(f"Building {name} with features: {features}")
    
    # 构建命令
    cmd = [
        "maturin", "build", 
        "--release",
        f"--features={','.join(features)}",
        "-o", "dist",
        "--compatibility", "off"
    ]
    
    # 设置包名环境变量
    env = {"MATURIN_PACKAGE_NAME": name}
    
    try:
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        print(f"✅ {name} built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} build failed: {e.stderr}")
        return False

def main():
    """Build all variants"""
    config_file = Path("build-variants.toml")
    if not config_file.exists():
        print("❌ build-variants.toml not found")
        return 1
        
    config = toml.load(config_file)
    success_count = 0
    
    for variant in config["variants"]:
        if build_variant(variant["name"], variant["features"], variant["description"]):
            success_count += 1
    
    print(f"\n📦 Built {success_count}/{len(config['variants'])} variants successfully")
    return 0 if success_count == len(config["variants"]) else 1

if __name__ == "__main__":
    sys.exit(main())
```

### Step 5: 更新pyproject.toml
```toml
# 新的 pyproject.toml
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "opendal"  # 默认包名，可通过环境变量覆盖
dynamic = ["version", "description"]
requires-python = ">=3.10"
authors = [
    {name = "Apache OpenDAL", email = "dev@opendal.apache.org"},
]
license = {text = "Apache-2.0"}
readme = "README.md"
keywords = ["storage", "rust", "s3", "azure", "gcs"]

[project.urls]
Homepage = "https://opendal.apache.org/"
Documentation = "https://opendal.apache.org/docs/python/"
Repository = "https://github.com/apache/opendal"

[tool.maturin]
bindings = "pyo3"
features = ["pyo3/extension-module"]
module-name = "opendal._opendal"
python-source = "python"
strip = true

# 可选依赖保持不变
[project.optional-dependencies]
benchmark = ["boto3>=1.37.9", "boto3-stubs[essential]>=1.37.9"]
dev = ["maturin>=1.8.2"]
test = ["pytest>=8.3.5", "pytest-asyncio>=0.25.3"]
```

### Step 6: 创建包描述配置
创建 `package-descriptions.toml`:

```toml
[packages]
[packages.opendal-core]
description = "Apache OpenDAL™ Python Core Binding - Essential Storage Services"
long_description = """
Core package with 15 essential storage services including:
- Local filesystem (fs) 
- Amazon S3 compatible services
- Azure Blob Storage
- Google Cloud Storage
- HTTP-based storage
- In-memory storage
Perfect for basic storage needs with minimal package size.
"""

[packages.opendal-database]  
description = "Apache OpenDAL™ Python Database Binding - Core + Database Services"
long_description = """
Includes all core services plus database and key-value store services:
- Redis, PostgreSQL, MySQL, SQLite
- RocksDB, Sled embedded databases
- Perfect for applications with database storage needs
"""

[packages.opendal-cloud]
description = "Apache OpenDAL™ Python Cloud Binding - Core + Cloud Services" 
long_description = """
Includes all core services plus cloud platform services:
- Dropbox, Google Drive, OneDrive
- Box, pCloud, Yandex Disk
- Perfect for applications with cloud storage integration
"""

[packages.opendal-advanced]
description = "Apache OpenDAL™ Python Advanced Binding - Core + Advanced Services"
long_description = """
Includes all core services plus advanced distributed services:
- TiKV, FoundationDB, etcd
- Consul, MinIO, Seafile  
- Perfect for distributed and enterprise applications
"""

[packages.opendal]
description = "Apache OpenDAL™ Python Binding - Complete Package"
long_description = """
Complete package with all 50+ storage services.
Includes core, database, cloud, and advanced services.
Perfect for full-featured applications.
"""
```

---

## 构建和测试

### 构建所有变体
```bash
# 安装依赖
pip install maturin toml

# 构建所有变体包
python scripts/build-variants.py

# 预期输出
# ✅ opendal-core built successfully (opendal_core-0.46.0-*.whl, ~10MB)
# ✅ opendal-database built successfully (opendal_database-0.46.0-*.whl, ~15MB)  
# ✅ opendal-cloud built successfully (opendal_cloud-0.46.0-*.whl, ~20MB)
# ✅ opendal-advanced built successfully (opendal_advanced-0.46.0-*.whl, ~25MB)
# ✅ opendal built successfully (opendal-0.46.0-*.whl, ~50MB)
```

### 测试用户体验
```bash
# 测试基础包
pip install dist/opendal_core-0.46.0-*.whl
python -c "import opendal; op = opendal.Operator('fs', root='/tmp'); print('✅ Core works')"
python -c "import opendal; opendal.Operator('redis')" # 应该报错

# 测试数据库包  
pip install dist/opendal_database-0.46.0-*.whl --force-reinstall
python -c "import opendal; op = opendal.Operator('redis', host='localhost'); print('✅ Database works')"
```

---

## 验证检查清单

### 功能验证
- [ ] 每个包都能独立安装
- [ ] API完全一致：`import opendal` 在所有包中工作
- [ ] 服务正确分类：core包只有核心服务，database包包含数据库服务
- [ ] 包大小符合预期：core~10MB, database~15MB等
- [ ] 错误处理：使用未包含服务时给出清晰错误提示

### 兼容性验证
- [ ] 现有用户代码无需修改
- [ ] 所有测试在不同包变体下都能通过
- [ ] 文档和示例在所有包中都正确工作

### 构建验证
- [ ] 构建脚本能成功构建所有变体
- [ ] CI/CD流程能正确构建和发布多个包
- [ ] 包名和版本正确设置

---

## 回滚方案

如果方案1遇到技术问题，可以快速回滚：

```bash
# 恢复原始配置
cp Cargo.toml.backup Cargo.toml
cp pyproject.toml.backup pyproject.toml

# 删除新增文件
rm build-variants.toml package-descriptions.toml
rm -rf scripts/

# 重新构建原始包
maturin build --features=services-all
```

---

## 下一步

1. **实施基础结构**：按照Step 1-5创建基础配置
2. **验证核心功能**：确保基础构建能够工作
3. **完善构建脚本**：优化构建流程和错误处理
4. **全面测试**：在不同环境测试所有包变体
5. **更新CI/CD**：配置自动化构建和发布流程

这个方案保持了workspace的优雅性，同时实现了按需安装的目标。你觉得这个实施方案如何？需要调整哪些部分？