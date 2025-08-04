# OpenDAL Core Python Binding

This package provides Python bindings for OpenDAL's core storage services.

## Included Services

This package includes 15 basic storage services:

### Cloud Storage
- **s3** - Amazon S3 compatible storage
- **gcs** - Google Cloud Storage  
- **azblob** - Azure Blob Storage
- **azdls** - Azure Data Lake Storage
- **cos** - Tencent Cloud Object Storage
- **obs** - Huawei Object Storage Service
- **oss** - Alibaba Cloud Object Storage Service

### Basic Services
- **fs** - Local filesystem
- **memory** - In-memory storage
- **http** - HTTP-based storage

### Enterprise/Specialized
- **webdav** - WebDAV protocol
- **webhdfs** - Hadoop WebHDFS
- **ghac** - GitHub Actions Cache
- **ipmfs** - IPFS Pinning Service

## Installation

```bash
pip install opendal-core
```

## Usage

```python
import opendal_core

# Create operators for core services
op = opendal_core.Operator("s3", bucket="my-bucket", region="us-east-1")
op.write("test.txt", b"Hello World")
content = op.read("test.txt")
```

## Note

This is a subset package of the full OpenDAL Python binding. For additional services:

- `opendal-database` - Database and key-value storage services
- `opendal-cloud` - Additional cloud platform services  
- `opendal-advanced` - Advanced and specialized services
- `opendal` - Meta-package with all services