"""Command-line interface for delong_datasets."""
import argparse
import json
import sys

from .api import DownloadOptions, download_dataset, export_data


def main(argv=None) -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="delong-datasets",
        description="Delong life-science datasets CLI - secure dataset access for TEE environments",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Download command
    p_dl = sub.add_parser("download", help="Download and display dataset (preview mode)")
    p_dl.add_argument("dataset_id", help="Dataset ID, e.g. medical_imaging_2024")
    p_dl.add_argument("--token", required=True, help="JWT bearer token")
    p_dl.add_argument("--stream", action="store_true", help="Enable streaming mode (lazy loading)")
    p_dl.add_argument("--columns", help="Comma-separated list of columns to fetch, e.g. 'patient_id,diagnosis'")
    p_dl.add_argument("--limit", type=int, help="Maximum number of rows to fetch")
    p_dl.add_argument("--preview", type=int, default=5, help="Number of rows to preview (default: 5)")

    # Export command
    p_exp = sub.add_parser("export", help="Download and export dataset to file")
    p_exp.add_argument("dataset_id", help="Dataset ID")
    p_exp.add_argument("--token", required=True, help="JWT bearer token")
    p_exp.add_argument("--format", required=True, choices=["csv", "json"], help="Export format")
    p_exp.add_argument("--output", required=True, help="Output file path")
    p_exp.add_argument("--columns", help="Comma-separated list of columns to export")
    p_exp.add_argument("--limit", type=int, help="Maximum number of rows to export")

    args = parser.parse_args(argv)

    try:
        if args.cmd == "download":
            columns = args.columns.split(",") if args.columns else None
            opts = DownloadOptions(stream=args.stream, columns=columns, limit=args.limit)
            data = download_dataset(args.dataset_id, args.token, opts)

            # Show preview
            if hasattr(data, "select") and hasattr(data, "num_rows"):
                rows = min(args.preview, getattr(data, "num_rows", args.preview) or args.preview)
                print(f"Dataset loaded: {data.num_rows} rows, {len(data.column_names)} columns")
                print(f"Columns: {data.column_names}")
                print(f"\nPreview (first {rows} rows):")
                print(data.select(range(rows)))
            else:
                # iterable dataset: take preview
                print("Streaming dataset (preview mode)")
                for i, ex in enumerate(data.take(args.preview)):
                    print(f"Row {i}: {ex}")
            return 0

        if args.cmd == "export":
            columns = args.columns.split(",") if args.columns else None
            opts = DownloadOptions(stream=False, columns=columns, limit=args.limit)
            data = download_dataset(args.dataset_id, args.token, opts)
            export_data(data, format=args.format, path=args.output)
            rows = getattr(data, "num_rows", "unknown")
            print(f"Exported {rows} rows to {args.output}")
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


