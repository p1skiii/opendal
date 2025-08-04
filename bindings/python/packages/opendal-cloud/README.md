# OpenDAL Cloud Services

This package provides Python bindings for OpenDAL extended cloud storage services.

## Supported Services

### Personal Cloud Storage
- Aliyun Drive
- Dropbox
- OneDrive
- Google Drive
- pCloud
- Yandex Disk

### Object Storage
- Backblaze B2
- Baidu BOS
- OpenStack Swift
- UpYun

### Specialized Cloud Services
- Cloudflare KV
- Cloudflare D1
- Vercel Artifacts
- GitHub (as storage)

### Developer Platforms
- Hugging Face
- Supabase
- LakeFS
- Seafile

### Distributed & Other Services
- IPFS
- ChainSafe
- Koofr
- CompFS
- LibSQL
- Moka (in-memory cache)
- DashMap

## Installation

```bash
pip install opendal-cloud
```

## Usage

```python
import opendal_cloud

# Dropbox example
op = opendal_cloud.Operator("dropbox", access_token="your_token")
op.write("file.txt", b"Hello World")
print(op.read("file.txt"))

# B2 example
op = opendal_cloud.Operator("b2", 
    bucket="your-bucket",
    application_key_id="your-key-id",
    application_key="your-key")
```

For more examples, see the [OpenDAL documentation](https://opendal.apache.org/docs/python/).
