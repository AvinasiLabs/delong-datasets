# delong-datasets

Python library for accessing sensitive life sciences datasets with TEE (Trusted Execution Environment) security controls.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

---

## Overview

**delong-datasets** provides a unified SSE (Server-Sent Events) streaming interface on top of HuggingFace `datasets`, supporting:

- **📡 Unified SSE endpoint**: one endpoint for both raw data and SQL query results
- **🧮 Server-side SQL (DuckDB)**: compute on the server, stream result sets only
- **📊 Flexible access**: column filtering (`columns`), offset/limit, optional streaming iteration
- **🧰 Developer-friendly**: `datasets`-compatible API, CLI, and examples

---

## Quick Start

### Installation

```bash
# Clone repository
git clone git@github.com:AvinasiLabs/delong-datasets.git
cd delong-datasets

# Install in development mode
pip install -e .
```

### Basic Usage

```python
from delong_datasets import download_dataset

# Download dataset (automatic TEE detection)
data = download_dataset("medical_imaging_2024", token="your-token")

print(f"Loaded {data.num_rows} rows")
print(data.column_names)

# Convert to pandas
import pandas as pd
df = pd.DataFrame(data)
print(df.head())
```

### Command Line

```bash
# Set environment
export TOKEN="your-access-token"

# Download dataset
python -m delong_datasets download dataset-id --token $TOKEN
```

---

## Key Features

### Unified SSE + SQL
Via the unified `GET /datasets/decrypt-stream` endpoint:
- Without `query`: raw data is streamed via `metadata/chunk/done` events
- With `query`: SQL is executed server-side (DuckDB) and only the result set is streamed

### Column Filtering

Request only the columns you need:

```python
from delong_datasets import download_dataset, DownloadOptions

opts = DownloadOptions(columns=["patient_id", "diagnosis"])
data = download_dataset("medical_imaging_2024", token, opts)
```

### Streaming Large Datasets

Process datasets that don't fit in memory:

```python
opts = DownloadOptions(stream=True)
dataset = download_dataset("large_genomics_data", token, opts)

for batch in dataset.iter(batch_size=1000):
    process(batch)
```

### Multiple Export Formats

```python
from delong_datasets import export_data

# Export to CSV, JSON, or Parquet
export_data(data, format="csv", path="/tmp/output.csv")
export_data(data, format="parquet", path="/tmp/output.parquet")
```

### SQL Query
Let the server perform aggregation/filtering to reduce network transfer:

```python
from delong_datasets import download_dataset, DownloadOptions

opts = DownloadOptions(
    query="SELECT sex, COUNT(*) AS count FROM data GROUP BY sex"
)
data = download_dataset("medical_imaging_2024", token, opts)
```

---

## Documentation

📚 **[Complete User Guide](USER_GUIDE.md)** - Comprehensive documentation covering all features

📖 **[Quick Start Guide](QUICKSTART.md)** - Step-by-step testing guide with mock services

🏗️ **[Architecture](ARCHITECTURE.md)** - System design and security model

🔄 **[Migration Guide](MIGRATION_GUIDE.md)** - Upgrading from previous versions

💡 **[Examples](examples/)** - Runnable code examples for common tasks

---

## Documentation Quick Links

### Getting Started
- [Installation](USER_GUIDE.md#installation)
- [Quick Start](USER_GUIDE.md#quick-start)
- [Basic Usage](USER_GUIDE.md#basic-usage)

### Features
- [Column Filtering](USER_GUIDE.md#column-filtering)
- [Pagination](USER_GUIDE.md#pagination)
- [Streaming Mode](USER_GUIDE.md#streaming-mode)
- [Data Export](USER_GUIDE.md#exporting-data)

### Advanced
- [Configuration](USER_GUIDE.md#configuration)
- [Security Model](USER_GUIDE.md#security-model)
- [API Reference](USER_GUIDE.md#api-reference)
- [Best Practices](USER_GUIDE.md#best-practices)
- [Troubleshooting](USER_GUIDE.md#troubleshooting)

---

## Examples

### Basic Download

```python
from delong_datasets import download_dataset

data = download_dataset("demo-dataset-001", "your-token")
print(f"Loaded {data.num_rows} rows")
```

### With Options

```python
from delong_datasets import download_dataset, DownloadOptions

opts = DownloadOptions(
    columns=["patient_id", "diagnosis", "age"],
    limit=100,
    stream=False
)
data = download_dataset("medical_imaging_2024", "your-token", opts)
```

### Pagination

```python
page_size = 1000
offset = 0

while True:
    opts = DownloadOptions(limit=page_size, offset=offset)
    page = download_dataset("large-dataset", token, opts)

    if page.num_rows == 0:
        break

    process(page)
    offset += page_size
```

### Export

```python
from delong_datasets import export_data

export_data(data, format="csv", path="/tmp/output.csv")
```

See the [examples directory](examples/) for more comprehensive examples.

---

## Access Control
The backend uses JWT for authentication/authorization and streams data over SSE. Column filtering, pagination, and server-side SQL are supported. Operators can configure IP allowlists and ownership checks on the server. See the “SSE Data Access” section in the User Guide.

---

## Development

### Setup

```bash
# Clone repository
git clone git@github.com:AvinasiLabs/delong-datasets.git
cd delong-datasets

# Install in development mode
pip install -e .
```

---

## Requirements

- **Python**: 3.9 or higher
- **Dependencies**:
  - `datasets >= 2.14` (HuggingFace datasets library)
- **Optional**:
  - `pandas` for DataFrame operations
  - `pyarrow` for Parquet support

---

## Configuration

Configure via environment variables:

```bash
# Authentication (required)
export TOKEN="your-access-token"

# Optional: Performance tuning
export DS_TIMEOUT=60
export DS_MAX_RETRIES=5
export DS_DEFAULT_LIMIT=5000
# Endpoint (optional; otherwise derived from DS_API_BASE_URL)
export DS_DECRYPT_STREAM_ENDPOINT="https://your-host/datasets/decrypt-stream"
```

See [Configuration Guide](USER_GUIDE.md#configuration) for all options.

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution

- 📝 Documentation improvements
- 🐛 Bug reports and fixes
- ✨ Feature requests and implementations
- 📚 Additional examples
- 🧪 Test coverage improvements

---

## Support

- **Documentation**: [USER_GUIDE.md](USER_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/delong-datasets/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/delong-datasets/discussions)

---

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

## Acknowledgments

This library is built on top of [🤗 Datasets](https://github.com/huggingface/datasets) by HuggingFace, which provides the foundational dataset loading and processing capabilities.

### Citation

If you use this library in your research, please cite both delong-datasets and the underlying HuggingFace Datasets library:

**HuggingFace Datasets:**

```bibtex
@inproceedings{lhoest-etal-2021-datasets,
    title: "huggingface/datasets"
    authors:
    - family-names: Lhoest
      given-names: Quentin
    - family-names: Villanova del Moral
      given-names: Albert
      orcid: "https://orcid.org/0000-0003-1727-1045"
    - family-names: von Platen
      given-names: Patrick
    - family-names: Wolf
      given-names: Thomas
    - family-names: Šaško
      given-names: Mario
    - family-names: Jernite
      given-names: Yacine
    - family-names: Thakur
      given-names: Abhishek
    - family-names: Tunstall
      given-names: Lewis
    - family-names: Patil
      given-names: Suraj
    - family-names: Drame
      given-names: Mariama
    - family-names: Chaumond
      given-names: Julien
    - family-names: Plu
      given-names: Julien
    - family-names: Davison
      given-names: Joe
    - family-names: Brandeis
      given-names: Simon
    - family-names: Sanh
      given-names: Victor
    - family-names: Le Scao
      given-names: Teven
    - family-names: Canwen Xu
      given-names: Kevin
    - family-names: Patry
      given-names: Nicolas
    - family-names: Liu
      given-names: Steven
    - family-names: McMillan-Major
      given-names: Angelina
    - family-names: Schmid
      given-names: Philipp
    - family-names: Gugger
      given-names: Sylvain
    - family-names: Raw
      given-names: Nathan
    - family-names: Lesage
      given-names: Sylvain
    - family-names: Lozhkov
      given-names: Anton
    - family-names: Carrigan
      given-names: Matthew
    - family-names: Matussière
      given-names: Théo
    - family-names: von Werra
      given-names: Leandro
    - family-names: Debut
      given-names: Lysandre
    - family-names: Bekman
      given-names: Stas
    - family-names: Delangue
      given-names: Clément
    doi: 10.5281/zenodo.4817768
    repository-code: "https://github.com/huggingface/datasets"
    license: Apache-2.0
    preferred-citation:
      type: conference-paper
      title: "Datasets: A Community Library for Natural Language Processing"
      authors:
      - family-names: Lhoest
        given-names: Quentin
      - family-names: Villanova del Moral
        given-names: Albert
        orcid: "https://orcid.org/0000-0003-1727-1045"
      - family-names: von Platen
        given-names: Patrick
      - family-names: Wolf
        given-names: Thomas
      - family-names: Šaško
        given-names: Mario
      - family-names: Jernite
        given-names: Yacine
      - family-names: Thakur
        given-names: Abhishek
      - family-names: Tunstall
        given-names: Lewis
      - family-names: Patil
        given-names: Suraj
      - family-names: Drame
        given-names: Mariama
      - family-names: Chaumond
        given-names: Julien
      - family-names: Plu
        given-names: Julien
      - family-names: Davison
        given-names: Joe
      - family-names: Brandeis
        given-names: Simon
      - family-names: Sanh
        given-names: Victor
      - family-names: Le Scao
        given-names: Teven
      - family-names: Canwen Xu
        given-names: Kevin
      - family-names: Patry
        given-names: Nicolas
      - family-names: Liu
        given-names: Steven
      - family-names: McMillan-Major
        given-names: Angelina
      - family-names: Schmid
        given-names: Philipp
      - family-names: Gugger
        given-names: Sylvain
      - family-names: Raw
        given-names: Nathan
      - family-names: Lesage
        given-names: Sylvain
      - family-names: Lozhkov
        given-names: Anton
      - family-names: Carrigan
        given-names: Matthew
      - family-names: Matussière
        given-names: Théo
      - family-names: von Werra
        given-names: Leandro
      - family-names: Debut
        given-names: Lysandre
      - family-names: Bekman
        given-names: Stas
      - family-names: Delangue
        given-names: Clément
      collection-title: "Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing: System Demonstrations"
      collection-type: proceedings
      month: 11
      year: 2021
      publisher:
        name: "Association for Computational Linguistics"
      url: "https://aclanthology.org/2021.emnlp-demo.21"
      start: 175
      end: 184
      identifiers:
        - type: other
          value: "arXiv:2109.02846"
          description: "The arXiv preprint of the paper"
}
```

---

**Ready to get started?** Check out the [Quick Start Guide](QUICKSTART.md) or dive into the [User Guide](USER_GUIDE.md)!
