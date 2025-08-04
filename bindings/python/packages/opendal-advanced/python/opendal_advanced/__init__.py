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
OpenDAL Advanced Services Package

Provides access to specialized and advanced storage services including:
- Network file systems: FTP, SFTP, WebDAV
- Distributed file systems: HDFS
- Specialized protocols: Apache Arrow Flight, AtomicServer
- Enhanced file systems: Azure File, DBFS, MonoioFS
- Advanced cache systems: Mini-Moka
"""

from ._opendal_advanced import *

__all__ = _opendal_advanced.__all__
