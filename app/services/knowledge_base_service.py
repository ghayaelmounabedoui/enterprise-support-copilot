import os
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv


load_dotenv()

KNOWLEDGE_BASE_ID = os.getenv(
    "BEDROCK_KNOWLEDGE_BASE_ID",
    "20NXSZ5UAO",
)

KNOWLEDGE_BASE_REGION = os.getenv(
    "BEDROCK_KNOWLEDGE_BASE_REGION",
    "eu-west-1",
)

bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=KNOWLEDGE_BASE_REGION,
)


def search_knowledge_base(
    query: str,
    number_of_results: int = 5,
) -> dict[str, Any]:
    """
    Search the Amazon Bedrock Knowledge Base and return
    the most relevant document passages.
    """

    cleaned_query = query.strip()

    if not cleaned_query:
        return {
            "found": False,
            "query": query,
            "results": [],
            "error": "The query cannot be empty.",
        }

    try:
        response = bedrock_agent_runtime.retrieve(
    knowledgeBaseId=KNOWLEDGE_BASE_ID,
    retrievalQuery={
        "text": cleaned_query,
    },
    retrievalConfiguration={
        "managedSearchConfiguration": {
            "numberOfResults": number_of_results
        }
    },
)

        retrieval_results = response.get("retrievalResults", [])

        formatted_results: list[dict[str, Any]] = []

        for result in retrieval_results:
            content = result.get("content", {})
            location = result.get("location", {})

            s3_location = location.get("s3Location", {})

            formatted_results.append(
                {
                    "text": content.get("text", ""),
                    "score": result.get("score"),
                    "source": s3_location.get("uri"),
                    "metadata": result.get("metadata", {}),
                }
            )

        return {
            "found": bool(formatted_results),
            "query": cleaned_query,
            "results": formatted_results,
        }

    except ClientError as exc:
        error = exc.response.get("Error", {})

        raise RuntimeError(
            f"Knowledge Base error: "
            f"{error.get('Code', 'UnknownError')} - "
            f"{error.get('Message', 'Unable to retrieve documents.')}"
        ) from exc

    except BotoCoreError as exc:
        raise RuntimeError(
            "Unable to communicate with the Amazon Bedrock Knowledge Base."
        ) from exc