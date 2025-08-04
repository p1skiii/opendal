# OpenDAL Advanced Services

This package provides Python bindings for OpenDAL specialized and advanced storage services.

## Supported Services

### Network File Systems
- **FTP** - File Transfer Protocol
- **SFTP** - SSH File Transfer Protocol  
- **WebDAV** - Web Distributed Authoring and Versioning

### Distributed File Systems
- **HDFS** - Hadoop Distributed File System

### Cloud File Systems
- **Azure File** - Azure File Storage
- **DBFS** - Databricks File System
- **MonoioFS** - Monoio-based file system

### Specialized Protocols
- **Apache Arrow Flight** - High-performance data transport
- **AtomicServer** - Atomic data storage
- **Nebula Graph** - Graph database storage

### Advanced Cache Systems
- **Mini-Moka** - High-performance in-memory cache

### Enhanced Variants
- **OBS Default** - Enhanced Huawei OBS
- **S3 Default** - Enhanced S3 with additional features

## Installation

```bash
pip install opendal-advanced
```

## Usage

```python
import opendal_advanced

# WebDAV example
op = opendal_advanced.Operator("webdav", 
    endpoint="https://your-webdav-server.com",
    username="user",
    password="pass")
op.write("file.txt", b"Hello World")

# SFTP example  
op = opendal_advanced.Operator("sftp",
    endpoint="sftp://your-server.com",
    username="user", 
    password="pass")

# HDFS example
op = opendal_advanced.Operator("hdfs",
    name_node="hdfs://namenode:9000",
    root="/user/data/")
```

For more examples, see the [OpenDAL documentation](https://opendal.apache.org/docs/python/).
