# OpenDAL Python Bindings Package Splitting Proposal

## Background & Problem

The current OpenDAL Python package (`opendal`) is approximately **50MB** in size because it includes all 50+ storage services (S3, Redis, Google Drive, DropBox, etc.). This creates a problem for users who only need basic functionality:

- A user who only needs filesystem and S3 access still downloads 50MB
- Most users (~70%) only use core services like fs, s3, memory, http
- The large package size affects installation time and deployment size

## Goal

Enable users to install only the services they need, reducing package size from 50MB to ~10MB for basic users, while maintaining 100% API compatibility.

---

## Solution 1: Workspace Multi-Feature Packages (Recommended)

### Core Concept
Build different **combination packages** from the same codebase using different feature sets. Each package contains core services plus specific additional services.

### Package Structure
```
opendal-core      (10MB)  - Core services: fs, s3, memory, http, azblob
opendal-database  (15MB)  - Core + Database: redis, mysql, postgresql  
opendal-cloud     (20MB)  - Core + Cloud: dropbox, gdrive, onedrive
opendal           (50MB)  - Complete package with all services
```

### Build Process
```bash
# Build different feature combinations
maturin build --features=services-core --package-name=opendal-core
maturin build --features=services-core,services-database --package-name=opendal-database
maturin build --features=services-core,services-cloud --package-name=opendal-cloud  
maturin build --features=services-all --package-name=opendal
```

### User Experience
```python
# User chooses appropriate package
pip install opendal-core        # Basic user: 10MB
pip install opendal-database    # Database user: 15MB
pip install opendal-cloud       # Cloud user: 20MB
pip install opendal            # Power user: 50MB

# API remains identical across all packages
import opendal
op = opendal.Operator("s3", bucket="my-bucket")    # Works in all packages
op = opendal.Operator("redis", host="localhost")   # Only works in database/full packages
```

### Technical Implementation
```
bindings/python/
├── Cargo.toml                 # Workspace with shared dependencies
├── pyproject.toml            # Build configuration for all variants
├── src/
│   ├── lib.rs               # Main binding code
│   ├── capability.rs        # Shared across all packages
│   └── ...                  # Other shared modules
└── features/
    ├── core.toml            # Core services definition
    ├── database.toml        # Database services definition
    └── cloud.toml           # Cloud services definition
```

---

## Solution 2: Hybrid Multi-Package with API Router

### Core Concept
Split into separate **independent packages** with a Python router package that provides unified API.

### Package Structure
```
opendal-core      (8MB)   - Core services only (Rust binary)
opendal-database  (5MB)   - Database services only (Rust binary)  
opendal-cloud     (7MB)   - Cloud services only (Rust binary)
opendal           (1MB)   - Python router package (depends on above)
```

### Build Process
```bash
# Build each package independently
cd packages/opendal-core && maturin build      # → opendal-core package 
cd packages/opendal-database && maturin build  # → opendal-database package
cd packages/opendal-cloud && maturin build     # → opendal-cloud package
cd packages/opendal && python -m build         # → opendal router package (pure Python)
```

### User Experience
```python
# User installs multiple packages as needed
pip install opendal-core                    # Basic: 8MB
pip install opendal-core opendal-database   # Database: 8MB + 5MB = 13MB
pip install opendal                         # Router + all dependencies: ~20MB

# API looks identical but routes internally
import opendal
op = opendal.Operator("s3", bucket="my-bucket")    # Routes to opendal-core
op = opendal.Operator("redis", host="localhost")   # Routes to opendal-database
```

### Technical Implementation
```
bindings/python/
├── Cargo.toml                    # Workspace configuration
├── packages/
│   ├── opendal-core/
│   │   ├── Cargo.toml           # Independent Rust package
│   │   ├── pyproject.toml       # Maturin build config
│   │   └── src/lib.rs           # Core services binding
│   ├── opendal-database/
│   │   ├── Cargo.toml           # Independent Rust package
│   │   └── src/lib.rs           # Database services binding
│   └── opendal/
│       ├── pyproject.toml       # Pure Python package
│       └── src/opendal/
│           └── __init__.py      # Router logic
```

Router implementation:
```python
# opendal/__init__.py
def Operator(service: str, **kwargs):
    if service in ["fs", "s3", "memory"]:
        from opendal_core._opendal_core import Operator as CoreOp
        return CoreOp(service, **kwargs)
    elif service in ["redis", "mysql"]:
        from opendal_database._opendal_database import Operator as DBOp
        return DBOp(service, **kwargs)
    # ... routing logic
```

---

## Detailed Comparison

### User Experience

| Aspect | Solution 1 (Multi-Feature) | Solution 2 (Multi-Package) |
|--------|----------------------------|----------------------------|
| **Package Selection** | Choose one package based on needs | Install multiple packages as needed |
| **Installation** | `pip install opendal-database` | `pip install opendal-core opendal-database opendal` |
| **API Consistency** | ✅ 100% identical | ✅ 100% identical (via routing) |
| **Import Statement** | `import opendal` | `import opendal` |
| **Package Management** | ✅ Simple (one package) | ❌ Complex (multiple packages) |
| **Upgrade Process** | ✅ `pip upgrade opendal-database` | ❌ Need to upgrade multiple packages |
| **Size for Basic User** | 10MB (opendal-core) | 8MB (opendal-core only) |
| **Size for DB User** | 15MB (opendal-database) | 13MB (core + database) |

### Development & CI/CD

| Aspect | Solution 1 (Multi-Feature) | Solution 2 (Multi-Package) |
|--------|----------------------------|----------------------------|
| **Build Complexity** | ❌ Multiple feature builds | ❌ Multiple package builds |
| **Build Time** | ❌ Longer (multiple full builds) | ✅ Shorter (parallel builds) |
| **Code Sharing** | ✅ Perfect (same codebase) | ⚠️ Good (workspace shared) |
| **Release Process** | ❌ Must release all variants | ✅ Can release independently |
| **Version Management** | ✅ Single version for all | ❌ Must sync multiple versions |
| **Testing** | ❌ Test all combinations | ❌ Test package interactions |
| **CI/CD Changes** | ⚠️ Moderate (build matrix) | ❌ Major (multi-package flow) |

### Project Ecosystem Impact

| Aspect | Solution 1 (Multi-Feature) | Solution 2 (Multi-Package) |
|--------|----------------------------|----------------------------|
| **PyPI Presence** | ❌ 4 similar package names | ✅ Clear package separation |
| **User Confusion** | ⚠️ Which package to choose? | ⚠️ Which packages needed? |
| **Documentation** | ⚠️ Explain package variants | ❌ Explain package combinations |
| **Third-party Integration** | ✅ Standard `opendal` dependency | ❌ Need to specify package sets |
| **Backward Compatibility** | ✅ Perfect (same API) | ✅ Perfect (same API) |
| **Community Fragmentation** | ✅ Low risk | ❌ Higher risk (partial installs) |

### Technical Risks

| Aspect | Solution 1 (Multi-Feature) | Solution 2 (Multi-Package) |
|--------|----------------------------|----------------------------|
| **Implementation Complexity** | ✅ Low (feature flags) | ❌ High (router + multi-build) |
| **Runtime Performance** | ✅ Native (no routing) | ⚠️ Minor routing overhead |
| **Type Safety** | ✅ Full Rust type safety | ⚠️ Router introduces Python layer |
| **Error Handling** | ✅ Direct Rust errors | ⚠️ Router may mask errors |
| **Debugging** | ✅ Direct to Rust code | ❌ May need to trace through router |

---

## Recommendation

**Solution 1 (Multi-Feature Packages)** is recommended because:

1. **Simpler User Experience**: Users install one package, not multiple
2. **Lower Technical Risk**: Uses standard Rust feature flags, no complex routing
3. **Better Performance**: No Python routing layer overhead
4. **Easier Maintenance**: Single codebase, single API, standard build process
5. **Better Ecosystem**: Cleaner PyPI presence, less fragmentation risk

**Trade-offs accepted**:
- Slightly larger packages (includes core in each)
- More complex CI/CD build matrix
- Users must choose the right package upfront

**Next Steps**:
1. Define exact service groupings for each package variant
2. Set up feature flags in Cargo.toml
3. Configure build matrix for different package variants
4. Update documentation to guide package selection

---

*This proposal aims to reduce the OpenDAL Python package size by 70% for basic users while maintaining 100% API compatibility and minimizing ecosystem disruption.*