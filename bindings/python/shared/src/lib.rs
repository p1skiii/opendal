// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

// expose the opendal rust core as `core`.
// We will use `ocore::Xxx` to represents all types from opendal rust core.
pub use ::opendal as ocore;
use pyo3::prelude::*;

pub mod capability;
pub use capability::*;

pub mod layers;
pub use layers::*;

pub mod lister;
pub use lister::*;

pub mod metadata;
pub use metadata::*;

pub mod operator;
pub use operator::*;

pub mod file;
pub use file::*;

pub mod utils;
pub use utils::*;

pub mod errors;
pub use errors::*;

pub mod options;
pub use options::*;
