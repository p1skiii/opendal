# OpenDAL Database Services

This package provides Python bindings for OpenDAL database storage services.

## Supported Services

### SQL Databases
- MySQL
- PostgreSQL  
- SQLite

### NoSQL Databases
- MongoDB
- GridFS
- Redis

### Cache Systems
- Memcached

### Distributed Systems
- etcd
- FoundationDB
- TiKV
- SurrealDB

### Local Storage Engines
- RocksDB
- Sled
- Redb
- Persy

## Installation

```bash
pip install opendal-database
```

## Usage

```python
import opendal_database

# Redis example
op = opendal_database.Operator("redis", endpoint="redis://localhost:6379")
op.write("key", b"value")
print(op.read("key"))

# MySQL example
op = opendal_database.Operator("mysql", 
    endpoint="mysql://user:pass@localhost:3306/db",
    table="my_table")
```

For more examples, see the [OpenDAL documentation](https://opendal.apache.org/docs/python/).
