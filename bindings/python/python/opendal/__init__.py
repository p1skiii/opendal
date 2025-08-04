# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
OpenDAL Python Binding - Smart Router

This package automatically routes operations to the appropriate service package
based on the storage scheme being used.
"""

import sys
from typing import Any, Dict, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from opendal_core import Operator as CoreOperator, AsyncOperator as CoreAsyncOperator

# Service routing configuration
CORE_SERVICES: Set[str] = {
    "azblob", "azdls", "cos", "fs", "gcs", "ghac", "http", "ipmfs", 
    "memory", "obs", "oss", "s3", "webdav", "webhdfs"
}

DATABASE_SERVICES: Set[str] = {
    # SQL Databases (verified from backup)
    "mysql", "postgresql", "sqlite",
    # NoSQL Databases (verified from backup)
    "mongodb", "gridfs", "redis",
    # Cache Systems (verified from backup)
    "memcached",
    # Local Storage Engines (verified from backup)
    "sled", "redb", "persy"
    # Note: etcd, foundationdb, tikv, rocksdb excluded due to build issues
}

CLOUD_SERVICES: Set[str] = {
    # Personal Cloud Storage (verified from backup)
    "aliyun-drive", "dropbox", "onedrive", "gdrive", "yandex-disk",
    # Object Storage (verified from backup)
    "b2", "swift", "upyun",
    # Developer Platforms (verified from backup)
    "huggingface", "seafile",
    # Distributed & Other Services (verified from backup)
    "ipfs", "koofr", "moka", "dashmap",
    # Misc (verified from backup)
    "vercel-artifacts", "alluxio"
}

ADVANCED_SERVICES: Set[str] = {
    # File System Extensions (verified from backup)
    "azfile", "monoiofs",
    # Cache Systems (verified from backup)
    "mini-moka", "cacache"
    # Note: ftp, hdfs, sftp excluded due to build/platform issues
}

def _get_service_package(scheme: str) -> str:
    """Determine which package provides the given scheme."""
    if scheme in CORE_SERVICES:
        return "opendal_core"
    elif scheme in DATABASE_SERVICES:
        return "opendal_database" 
    elif scheme in CLOUD_SERVICES:
        return "opendal_cloud"
    elif scheme in ADVANCED_SERVICES:
        return "opendal_advanced"
    else:
        # Default to core for unknown schemes
        return "opendal_core"

def _import_operator(scheme: str):
    """Import the appropriate Operator class for the given scheme."""
    package_name = _get_service_package(scheme)
    
    try:
        if package_name == "opendal_core":
            from opendal_core import Operator, AsyncOperator
        elif package_name == "opendal_database":
            from opendal_database import Operator, AsyncOperator
        elif package_name == "opendal_cloud":
            from opendal_cloud import Operator, AsyncOperator
        elif package_name == "opendal_advanced":
            from opendal_advanced import Operator, AsyncOperator
        else:
            raise ImportError(f"Unknown package: {package_name}")
            
        return Operator, AsyncOperator
        
    except ImportError as e:
        # Provide helpful installation instructions
        if package_name == "opendal_core":
            # This should never happen as core is always installed
            raise ImportError(f"OpenDAL core package not found. Please reinstall: pip install opendal")
        elif package_name == "opendal_database":
            raise ImportError(f"Database services not installed. Install with: pip install opendal[database]")
        elif package_name == "opendal_cloud":
            raise ImportError(f"Cloud services not installed. Install with: pip install opendal[cloud]")  
        elif package_name == "opendal_advanced":
            raise ImportError(f"Advanced services not installed. Install with: pip install opendal[advanced]")
        else:
            raise e

class Operator:
    """Smart routing Operator that delegates to the appropriate service package."""
    
    def __new__(cls, scheme: str, **options: Any):
        """Create operator instance from the appropriate service package."""
        OperatorClass, _ = _import_operator(scheme)
        return OperatorClass(scheme, **options)

class AsyncOperator:
    """Smart routing AsyncOperator that delegates to the appropriate service package."""
    
    def __new__(cls, scheme: str, **options: Any):
        """Create async operator instance from the appropriate service package."""
        _, AsyncOperatorClass = _import_operator(scheme)
        return AsyncOperatorClass(scheme, **options)

# Import shared types and exceptions from core package
try:
    from opendal_core import (
        File, AsyncFile, Entry, EntryMode, Metadata, PresignedRequest, Capability,
        WriteOptions, ReadOptions, ListOptions, StatOptions
    )
    # Import submodules and make them available as opendal.exceptions and opendal.layers
    from opendal_core import exceptions as _exceptions, layers as _layers
    
    # Make submodules accessible via opendal.exceptions and opendal.layers
    import sys
    sys.modules['opendal.exceptions'] = _exceptions
    sys.modules['opendal.layers'] = _layers
    
    # Also make them available as attributes
    exceptions = _exceptions
    layers = _layers
    
except ImportError:
    raise ImportError("OpenDAL core package not found. Please install: pip install opendal")

# Export everything that the original opendal package exported
__all__ = [
    "Operator", "AsyncOperator", "File", "AsyncFile", "Entry", "EntryMode", 
    "Metadata", "PresignedRequest", "Capability", "WriteOptions", "ReadOptions", 
    "ListOptions", "StatOptions", "exceptions", "layers"
]