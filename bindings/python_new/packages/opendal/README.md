# OpenDAL

Apache OpenDAL™ Python Binding - Unified Data Access Layer

OpenDAL provides a unified data access layer, enabling seamless interaction with various storage services through a consistent API.

## Installation

```bash
# Install the main package (includes core services)
pip install opendal

# Install additional service packages as needed
pip install opendal-service-redis
pip install opendal-service-postgresql
pip install opendal-service-mongodb
```

## Quick Start

```python
import opendal

# Use default services (included in opendal-core)
op1 = opendal.Operator("fs", root="/tmp")
op2 = opendal.Operator("s3", bucket="my-bucket", region="us-east-1")

# Use optional services (requires separate installation)
op3 = opendal.Operator("redis://localhost:6379")  # Requires: pip install opendal-service-redis
```

## Supported Services

### Default Services (included)
- File System, S3, Azure Blob, Google Cloud Storage, Memory, and more

### Optional Services (separate packages)
- Redis, PostgreSQL, MongoDB, MySQL, SQLite, and more

## License

Licensed under the Apache License, Version 2.0.