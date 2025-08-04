# OpenDAL Core

Apache OpenDAL™ Python Binding - Core Package

This package provides the core OpenDAL Python bindings with default services including:
- File System (fs)
- S3 and S3-compatible services
- Azure Blob Storage (azblob)
- Google Cloud Storage (gcs)
- Memory storage
- And 10+ other default services

## Installation

```bash
pip install opendal-core
```

## Usage

```python
from opendal_core import Operator

# Create an operator
op = Operator("fs", root="/tmp")

# Write data
op.write("hello.txt", b"Hello, World!")

# Read data  
content = op.read("hello.txt")
print(content)  # b"Hello, World!"
```

## License

Licensed under the Apache License, Version 2.0.