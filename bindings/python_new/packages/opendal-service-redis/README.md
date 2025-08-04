# OpenDAL Service - Redis

Apache OpenDAL™ Python Binding - Redis Service Package

This package extends OpenDAL with Redis support.

## Installation

```bash
pip install opendal-service-redis
```

Note: This package requires `opendal-core` to be installed.

## Usage

```python
import opendal

# Create Redis operator
op = opendal.Operator("redis://localhost:6379")

# Use like any other OpenDAL operator
op.write("key", b"value")
content = op.read("key")
```

## License

Licensed under the Apache License, Version 2.0.