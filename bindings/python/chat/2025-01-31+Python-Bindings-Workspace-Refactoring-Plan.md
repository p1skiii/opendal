# Python Bindings Workspace Refactoring Plan
**Date**: 2025-01-31  
**Status**: Ready for Phase 1 Implementation

## 背景和目标

### 主要问题
当前的Python绑定采用单包结构，包含所有50+存储服务，导致：
- **包体积臃肿**：PyPI wheel文件巨大，下载时间长
- **用户体验差**：用户即使只需要S3服务，也要下载全部服务
- **资源浪费**：大量不必要的依赖和二进制代码

### 重构目标
将单包结构重构为workspace模式：
- **opendal-core**: 包含15个核心服务（fs, s3, gcs等）
- **opendal-service-***: 各个扩展服务包（redis, mongodb等）
- **opendal**: 元包，提供统一安装入口

### 预期收益
- 减少包体积，提升安装速度
- 按需安装服务，降低资源消耗
- 保持用户API完全兼容
- 符合Python生态最佳实践

## 技术分析

### 现有架构复杂性
通过深度分析发现，原始binding远比预想复杂：

#### 1. 代码生成系统
```
just generate python 
  ↓
cargo run --manifest-path=dev/Cargo.toml -- generate -l python
  ↓  
dev/src/generate/python.rs 读取core服务配置
  ↓
使用python.j2模板生成 bindings/python/python/opendal/__base.pyi
```

#### 2. 构建流程
```
uv build (maturin build)
  ↓
编译 bindings/python/src/*.rs (Rust代码)
  ↓
生成 _opendal.so 动态库
  ↓
放入 bindings/python/python/opendal/ 目录
```

#### 3. 关键配置文件
- **Cargo.toml**: 定义`services-all`特性用于PyPI wheel构建
- **pyproject.toml**: maturin配置，`module-name = "opendal._opendal"`
- **dev/src/generate/python.rs**: `enabled_service()`函数控制服务启用

#### 4. Python包结构
```
bindings/python/python/opendal/
├── __init__.py          # from ._opendal import *
├── __base.pyi          # 自动生成的类型定义
├── _opendal.so         # maturin编译的Rust模块
└── *.pyi               # 手写的类型定义文件
```

### 关键发现和注意事项

#### 1. 代码生成路径硬编码
`dev/src/generate/python.rs`第40行硬编码了路径：
```rust
let output = workspace_dir.join("bindings/python/python/opendal/__base.pyi");
```
**影响**: workspace重构后需要适配多包结构

#### 2. services-all特性的重要性
Cargo.toml中的注释：
```toml
# NOTE: this is the feature we used to build pypi wheels.
# When enable or disable some features,
# Also, you need to update the `enabled_service` function in dev/src/generate/python.rs to match it.
```
**影响**: 必须保持Cargo.toml和python.rs的服务配置同步

#### 3. maturin多包构建
原始配置使用单一的`module-name = "opendal._opendal"`，workspace需要：
```toml
[tool.maturin]
members = [
    "packages/opendal-core",
    "packages/opendal-redis", 
    "packages/opendal"
]
```

#### 4. 开发工具链
- **uv**: 包管理器和构建工具
- **maturin**: Rust-Python绑定构建后端
- **pytest**: 测试框架，通过环境变量控制服务：`OPENDAL_TEST=fs`

## 设计方案

### 目标workspace结构
```
bindings/python/
├── Cargo.toml                    # workspace root
├── pyproject.toml               # workspace Python config  
├── src/                         # 共享Rust源码 (保持不变)
├── python/                      # 原有Python包结构 (临时保持)
├── packages/
│   ├── opendal-core/           # 核心包 (15个基础服务)
│   │   ├── Cargo.toml
│   │   ├── pyproject.toml
│   │   └── python/
│   │       └── opendal_core/
│   ├── opendal-redis/          # Redis扩展包
│   │   ├── Cargo.toml
│   │   ├── pyproject.toml  
│   │   └── python/
│   │       └── opendal_redis/
│   └── opendal/               # 元包 (统一安装)
│       ├── pyproject.toml
│       └── python/
│           └── opendal/
├── tests/                      # 共享测试 (保持不变)
├── docs/                       # 共享文档 (保持不变)  
└── README.md                   # 需要更新
```

### 核心设计原则
1. **渐进式重构**: 每个阶段都保持功能完整可测试
2. **保持兼容性**: 用户API和导入方式不变
3. **工具链兼容**: 继续使用uv、maturin、pytest
4. **代码复用**: 最大程度复用现有Rust源码

## 实施计划

### Phase 1: 创建workspace基础 (保持100%兼容)
**目标**: 将单包结构转换为workspace，但功能完全不变

#### 1.1 修改根Cargo.toml
```toml
[workspace]
members = ["packages/opendal-temp"]  # 临时单一包
resolver = "2"

[workspace.dependencies]
# 将现有dependencies移到这里
bytes = "1.5.0"
chrono = "0.4"
# ... 其他依赖
```

#### 1.2 修改根pyproject.toml
```toml
[build-system]
build-backend = "maturin"
requires = ["maturin>=1.0,<2.0"]

[tool.maturin]
members = ["packages/opendal-temp"]

# 保持现有工具配置
[tool.ruff]
# ... 原有配置
```

#### 1.3 创建临时包
```
packages/opendal-temp/
├── Cargo.toml          # 完全复制现有配置
├── pyproject.toml      # 保持现有maturin配置
└── src/                # 链接到../../src/
```

#### 1.4 测试检查点
- `uv build` 成功构建
- `uv run pytest` 所有测试通过
- `just generate python` 正常工作
- Python导入 `import opendal` 正常

### Phase 2: 创建opendal-core包
**目标**: 创建包含核心服务的独立包

#### 2.1 创建opendal-core包
- 包含15个核心服务（基于原始Cargo.toml的default feature）
- 独立的Cargo.toml和pyproject.toml
- 正确的module-name配置

#### 2.2 适配代码生成
- 修改`dev/src/generate/python.rs`支持多个目标路径
- 更新`enabled_service()`函数匹配新结构

#### 2.3 测试检查点
- opendal-core包独立构建成功
- 核心服务功能完整
- 类型定义正确生成

### Phase 3: 拆分服务包
**目标**: 将扩展服务拆分为独立包

#### 3.1 创建服务包
- opendal-redis, opendal-mongodb等
- 每个包只包含特定服务
- 独立的feature配置

#### 3.2 更新构建配置
- 更新workspace members
- 调整代码生成配置
- 确保服务间无冲突

#### 3.3 测试检查点
- 各服务包独立功能正常
- 服务间不相互影响
- 性能无显著降低

### Phase 4: 创建元包和完善
**目标**: 提供统一的用户体验

#### 4.1 创建opendal元包
- 依赖所有子包
- 提供统一的导入接口
- 保持完全的API兼容

#### 4.2 更新文档和工具
- 更新README和docs
- 调整CI/CD配置
- 完善发布流程

#### 4.3 最终测试
- 完整功能测试
- 性能基准测试
- 用户场景验证

## 风险识别和缓解

### 主要风险
1. **代码生成路径问题**: 硬编码路径导致生成失败
   - 缓解：先修改python.rs支持配置化路径

2. **maturin多包构建复杂性**: workspace构建可能失败
   - 缓解：先创建最小化workspace验证可行性

3. **服务依赖冲突**: 不同服务包可能有依赖冲突
   - 缓解：使用workspace.dependencies统一管理

4. **性能回退**: 多包结构可能影响性能
   - 缓解：在每个阶段进行性能基准测试

### 回滚策略
每个Phase都保持原有结构完整，可以随时回滚到上一个稳定状态。

## 下一步行动

**立即开始Phase 1**:
1. 创建packages目录
2. 修改根Cargo.toml为workspace配置
3. 修改根pyproject.toml适配workspace
4. 创建opendal-temp包
5. 运行完整测试验证兼容性

**成功标准**: 
- 所有现有测试通过
- `uv build`成功
- Python导入功能正常
- 代码生成正常工作

---
*此文档记录了完整的分析过程和实施计划，继任者可以直接基于此开始Phase 1的工作。*