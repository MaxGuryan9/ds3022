# Columnar File Formats Beyond Parquet

Notes on why Parquet enables fast remote/selective reads (relevant to `query-benchmark.py`), and what else exists in this space.

## Why Parquet supports fast selective reads

Parquet files store a footer with schema info and byte offsets for every column chunk in every row group. A reader can:

1. Fetch just the footer (a small HTTP range request).
2. Use that metadata to find the exact byte ranges for the columns it needs.
3. Issue range requests for only those bytes — skipping unrequested columns entirely ("projection pushdown").

Row-group-level statistics (min/max per column) also let a filtered query skip whole row groups without reading them ("predicate pushdown"). For a query against a remote file (e.g. an HTTP/S3 URL), this pushdown saves actual network transfer time, not just local parsing time — which is why an engine that does this well (e.g. DuckDB) can look dramatically faster than one that doesn't, on a cold/uncached run.

CSV has none of this: no footer, no per-column byte offsets, no row-group stats, and values are interleaved row-by-row. So reading one column from a remote CSV generally requires fetching (and parsing) close to the whole file — no column-level or predicate pushdown at the transport layer.

## Direct alternatives to Parquet (columnar file formats)

- **Apache ORC (Optimized Row Columnar)** — conceptually similar to Parquet: column chunks, stripe-level statistics (min/max, bloom filters), footer metadata for pushdown. Favored historically in the Hive/Hadoop ecosystem; sometimes edges out Parquet on compression. Supported by DuckDB and most modern engines, but smaller tooling ecosystem than Parquet.

- **Apache Arrow / Feather (IPC format)** — Arrow's in-memory columnar layout serialized to disk. Not compressed as aggressively as Parquet and not designed for the same predicate/row-group pushdown. Its strength is zero-copy reads (mmap the file directly without deserialization) — great for fast local reads and cross-tool interop (e.g. Python to R), not for minimizing network bytes on a remote file.

- **Lance** — newer columnar format built for ML/vector workloads (embeddings, random access, versioning). Supports Parquet-like columnar pushdown plus native vector-search indexing. More relevant to ML data than typical tabular analytics.

## Table formats layered on top of Parquet

These aren't file formats themselves — they're metadata layers sitting on top of a collection of Parquet (usually) files:

- **Apache Iceberg**
- **Delta Lake**
- **Apache Hudi**

They maintain manifests of file-level and column-level statistics *across many files*, enabling pruning at the "which files do I even need to open" level — e.g. skipping 9,000 of 10,000 files instantly based on partition/column stats before issuing any byte-range request. DuckDB and Polars both have growing support for querying Iceberg/Delta tables directly. This is where the biggest "searchability" gains show up at scale — not from swapping the underlying file format, but from adding a table format on top when there are many files.

## Row-oriented formats, for contrast

- **Avro** — schema-embedded, splittable, well suited to write-heavy/streaming pipelines (e.g. Kafka). Row-oriented, so no column-pruning benefit like Parquet/ORC.

## Takeaway for a single-file benchmark

For a single-file analytics workload (e.g. aggregating a couple of columns from one taxi trip Parquet file), Parquet is already close to optimal. ORC would behave almost identically — same pushdown story, similar file size. The larger jump in searchability comes from adding a table format (Iceberg/Delta) on top when working with many files, not from picking a different single-file format.
