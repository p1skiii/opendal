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

import pytest
import opendal

# This test is the baseline check for the Operator object itself.

def test_capability_object_creation(operator):
    """
    Tests if the capability object can be created and is not None.
    This is the most basic health check.
    """
    cap = operator.capability()
    assert cap is not None

def test_capability_core_attributes(operator):
    """
    Tests if the capability object for the core profile (fs service)
    has the expected core capabilities.
    """
    cap = operator.capability()
    assert cap.read is True
    assert cap.write is True
    assert cap.list is True
    assert cap.scan is True

def test_capability_non_existent_attribute(operator):
    """
    Tests that accessing a non-existent capability raises an AttributeError.
    """
    cap = operator.capability()
    with pytest.raises(AttributeError):
        _ = cap.this_capability_does_not_exist
