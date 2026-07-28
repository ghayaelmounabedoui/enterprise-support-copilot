import json
import os
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError


AWS_REGION = os.getenv("AWS_REGION", "eu-west-3")
S3_BUCKET_NAME = os.getenv(
    "S3_BUCKET_NAME",
    "enterprise-support-copilot-data",
)

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
)


def load_json_from_s3(key: str) -> list[dict[str, Any]]:
    try:
        response = s3_client.get_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
        )

        content = response["Body"].read().decode("utf-8")
        data = json.loads(content)

        if not isinstance(data, list):
            raise ValueError(
                f"The S3 object '{key}' must contain a JSON list."
            )

        return data

    except ClientError as exc:
        error = exc.response.get("Error", {})
        code = error.get("Code", "S3Error")
        message = error.get("Message", "Unknown S3 error")

        raise RuntimeError(
            f"Unable to read s3://{S3_BUCKET_NAME}/{key}: "
            f"{code} - {message}"
        ) from exc

    except BotoCoreError as exc:
        raise RuntimeError(
            "Unable to communicate with Amazon S3."
        ) from exc

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"The S3 object '{key}' does not contain valid JSON."
        ) from exc


def save_json_to_s3(
    key: str,
    data: list[dict[str, Any]],
) -> None:
    body = json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
    ).encode("utf-8")

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=body,
            ContentType="application/json",
        )

    except ClientError as exc:
        error = exc.response.get("Error", {})
        code = error.get("Code", "S3Error")
        message = error.get("Message", "Unknown S3 error")

        raise RuntimeError(
            f"Unable to write s3://{S3_BUCKET_NAME}/{key}: "
            f"{code} - {message}"
        ) from exc

    except BotoCoreError as exc:
        raise RuntimeError(
            "Unable to communicate with Amazon S3."
        ) from exc