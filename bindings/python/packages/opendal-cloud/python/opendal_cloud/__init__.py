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
OpenDAL Cloud Services Package

Provides access to extended cloud storage services including:
- Cloud storage: Aliyun Drive, Dropbox, OneDrive, Google Drive
- Object storage: B2, Baidu BOS, Swift, UpYun
- Specialized services: Cloudflare KV, Vercel Artifacts, GitHub
- Developer platforms: Hugging Face, Supabase, LakeFS
"""

from ._opendal_cloud import *

__all__ = _opendal_cloud.__all__
