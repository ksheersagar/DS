"""Upload a file from a NAS mount path to Dell ECS (S3-compatible).

Example:
python nas_to_ecs.py \
  --nas-file /mnt/nas/data/report.csv \
  --bucket backup-bucket \
  --object-key reports/report.csv \
  --endpoint https://ecs.example.com \
  --access-key "$ECS_ACCESS_KEY" \
  --secret-key "$ECS_SECRET_KEY"
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError


def upload_file(
    nas_file: pathlib.Path,
    bucket: str,
    object_key: str,
    endpoint: str,
    access_key: str,
    secret_key: str,
    region: str = "us-east-1",
    verify_ssl: bool = True,
) -> None:
    if not nas_file.exists() or not nas_file.is_file():
        raise FileNotFoundError(f"NAS file does not exist or is not a regular file: {nas_file}")

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(signature_version="s3v4"),
        verify=verify_ssl,
    )

    s3.upload_file(str(nas_file), bucket, object_key)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Upload a NAS file to Dell ECS (S3-compatible).")
    parser.add_argument("--nas-file", required=True, type=pathlib.Path, help="Path to source file on NAS mount.")
    parser.add_argument("--bucket", required=True, help="Destination ECS bucket.")
    parser.add_argument("--object-key", required=True, help="Destination object key in ECS bucket.")
    parser.add_argument("--endpoint", required=True, help="Dell ECS S3 endpoint URL.")
    parser.add_argument("--access-key", required=True, help="ECS access key.")
    parser.add_argument("--secret-key", required=True, help="ECS secret key.")
    parser.add_argument("--region", default="us-east-1", help="AWS region name used by S3 client.")
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Disable SSL certificate verification (only for testing).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        upload_file(
            nas_file=args.nas_file,
            bucket=args.bucket,
            object_key=args.object_key,
            endpoint=args.endpoint,
            access_key=args.access_key,
            secret_key=args.secret_key,
            region=args.region,
            verify_ssl=not args.no_verify_ssl,
        )
    except (FileNotFoundError, BotoCoreError, ClientError) as exc:
        print(f"Upload failed: {exc}", file=sys.stderr)
        return 1

    print(f"Uploaded {args.nas_file} to s3://{args.bucket}/{args.object_key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
