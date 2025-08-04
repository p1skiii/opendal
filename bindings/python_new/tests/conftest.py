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

import os
from uuid import uuid4
import tempfile

import pytest
from dotenv import load_dotenv

# In the new architecture, all APIs are exposed under the top-level `opendal` package.
import opendal

# Load environment variables from .env file for testing different services.
load_dotenv()

# Use pytest-asyncio for async tests
pytest_plugins = ("pytest_asyncio",)


def pytest_configure(config):
    # Register an additional marker for capability-based test skipping.
    config.addinivalue_line(
        "markers",
        "need_capability(*capability): mark test to run only on named capability",
    )


@pytest.fixture(scope="session")
def service_name():
    """
    Fixture to get the service name from the OPENDAL_TEST environment variable.
    Skips tests if the variable is not set.
    """
    service_name = os.environ.get("OPENDAL_TEST")
    if service_name is None:
        pytest.skip("OPENDAL_TEST environment variable not set, skipping tests.")
    return service_name


@pytest.fixture(scope="session")
def setup_config(service_name):
    """
    Fixture to build the operator config from environment variables.
    Example: OPENDAL_S3_BUCKET -> {"bucket": "..."}
    """
    prefix = f"opendal_{service_name}_"
    config = {}
    for key, value in os.environ.items():
        if key.lower().startswith(prefix):
            config[key[len(prefix):].lower()] = value
            
    # Add a random root to avoid test interference, unless disabled.
    disable_random_root = os.environ.get("OPENDAL_DISABLE_RANDOM_ROOT") == "true"
    if not disable_random_root:
        # For fs service, we must physically create the directory.
        # For other services, this is just a prefix.
        root_path = os.path.join(config.get("root", tempfile.gettempdir()), str(uuid4()))
        if service_name == "fs":
            os.makedirs(root_path, exist_ok=True)
        config["root"] = root_path
        
    return config


@pytest.fixture(scope="session")
def async_operator(service_name, setup_config):
    """
    Create a fully configured async operator with standard layers for testing.
    """
    # The layers are now accessed via `opendal.layers`
    return (
        opendal.AsyncOperator(service_name, **setup_config)
        .layer(opendal.layers.RetryLayer())
    )


@pytest.fixture(scope="session")
def operator(async_operator):
    """
    Create a sync operator from the async one.
    """
    return async_operator.to_operator()


@pytest.fixture(autouse=True)
def check_capability(request, operator):
    """
    Auto-use fixture to skip tests based on the 'need_capability' marker.
    """
    marker = request.node.get_closest_marker("need_capability")
    if marker:
        capabilities = marker.args
        op_capability = operator.capability()
        for cap in capabilities:
            if not getattr(op_capability, cap, False):
                pytest.skip(
                    f"Service {operator.scheme} does not support capability: {cap}"
                )