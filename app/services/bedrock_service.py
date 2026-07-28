from typing import Any
import re

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import get_settings
from app.services.customer_service import get_customer
from app.services.knowledge_base_service import search_knowledge_base
from app.services.order_service import get_order
from app.services.refund_service import check_refund_eligibility


class BedrockService:
    def __init__(self) -> None:
        settings = get_settings()

        self.model_id = settings.bedrock_model_id

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
        )

        self.system_prompt = [
            {
                "text": (
                    "You are an enterprise customer support assistant. "
                    "Use company tools whenever the user requests company-specific "
                    "information. "
                    "\n\n"
                    "Tool selection rules:\n"
                    "- Use get_order when the user asks about a specific order.\n"
                    "- Use get_customer when the user asks directly about a specific "
                    "customer.\n"
                    "- Use get_order_with_customer when the user asks who is associated "
                    "with an order, or requests both order and customer information.\n"
                    "- Use check_refund_eligibility when the user asks whether a specific "
                    "order can be refunded or returned.\n"
                    "- Use search_knowledge_base for general questions about refund "
                    "policies, warranty policies, shipping rules, return conditions, "
                    "support FAQs, or company documentation.\n"
                    "\n"
                    "Examples:\n"
                    "- 'What is the refund policy?' -> search_knowledge_base.\n"
                    "- 'How long does a refund take?' -> search_knowledge_base.\n"
                    "- 'Can order ORD-84721 be refunded?' "
                    "-> check_refund_eligibility.\n"
                    "- 'What is the status of ORD-84721?' -> get_order.\n"
                    "- 'Who is associated with ORD-84721?' "
                    "-> get_order_with_customer.\n"
                    "\n"
                    "Never invent company policies, orders, customers, refund decisions, "
                    "or other company data. "
                    "Only use information returned by the tools. "
                    "When knowledge-base sources are available, briefly mention the "
                    "document name. "
                    "Return only the final answer to the user. "
                    "Never expose internal reasoning, analysis, or thinking tags."
                )
            }
        ]

        self.tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": "get_order",
                        "description": (
                            "Retrieve information about a specific order from "
                            "the company system."
                        ),
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "order_id": {
                                        "type": "string",
                                        "description": (
                                            "The exact order identifier, "
                                            "for example ORD-84721."
                                        ),
                                    }
                                },
                                "required": ["order_id"],
                            }
                        },
                    }
                },
                {
                    "toolSpec": {
                        "name": "get_customer",
                        "description": (
                            "Retrieve information about a specific customer "
                            "from the company system."
                        ),
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "customer_id": {
                                        "type": "string",
                                        "description": (
                                            "The exact customer identifier, "
                                            "for example CUST-1001."
                                        ),
                                    }
                                },
                                "required": ["customer_id"],
                            }
                        },
                    }
                },
                {
                    "toolSpec": {
                        "name": "get_order_with_customer",
                        "description": (
                            "Retrieve an order and the customer associated with it. "
                            "Use this tool when the user asks who owns an order or "
                            "requests both order and customer details."
                        ),
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "order_id": {
                                        "type": "string",
                                        "description": (
                                            "The exact order identifier, "
                                            "for example ORD-84721."
                                        ),
                                    }
                                },
                                "required": ["order_id"],
                            }
                        },
                    }
                },
                {
                    "toolSpec": {
                        "name": "check_refund_eligibility",
                        "description": (
                            "Check whether a specific order is eligible for a refund "
                            "according to company business rules. "
                            "Use this tool when the user asks whether an order "
                            "can be refunded or returned."
                        ),
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "order_id": {
                                        "type": "string",
                                        "description": (
                                            "The exact order identifier, "
                                            "for example ORD-84721."
                                        ),
                                    }
                                },
                                "required": ["order_id"],
                            }
                        },
                    }
                },
                {
                    "toolSpec": {
                        "name": "search_knowledge_base",
                        "description": (
                            "Search the company knowledge base for refund policies, "
                            "warranty policies, shipping rules, return conditions, "
                            "support FAQs, and other company documentation. "
                            "Use this tool for general policy questions."
                        ),
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": (
                                            "The complete user question to search "
                                            "in the company knowledge base."
                                        ),
                                    }
                                },
                                "required": ["query"],
                            }
                        },
                    }
                },
            ]
        }

    def _call_model(
        self,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return self.client.converse(
            modelId=self.model_id,
            system=self.system_prompt,
            messages=messages,
            toolConfig=self.tool_config,
            inferenceConfig={
                "maxTokens": 700,
                "temperature": 0.2,
                "topP": 0.9,
            },
        )

    def _execute_tool(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> dict[str, Any]:
        if tool_name == "get_order":
            order_id = str(tool_input.get("order_id", "")).strip()

            if not order_id:
                return {
                    "found": False,
                    "error": "The order_id parameter is required.",
                }

            order = get_order(order_id)

            if order is None:
                return {
                    "found": False,
                    "order_id": order_id,
                    "message": (
                        f"Order {order_id} was not found "
                        "in the company database."
                    ),
                }

            return {
                "found": True,
                "order": order,
            }

        if tool_name == "get_customer":
            customer_id = str(
                tool_input.get("customer_id", "")
            ).strip()

            if not customer_id:
                return {
                    "found": False,
                    "error": "The customer_id parameter is required.",
                }

            customer = get_customer(customer_id)

            if customer is None:
                return {
                    "found": False,
                    "customer_id": customer_id,
                    "message": (
                        f"Customer {customer_id} was not found "
                        "in the company database."
                    ),
                }

            return {
                "found": True,
                "customer": customer,
            }

        if tool_name == "get_order_with_customer":
            order_id = str(tool_input.get("order_id", "")).strip()

            if not order_id:
                return {
                    "found": False,
                    "error": "The order_id parameter is required.",
                }

            order = get_order(order_id)

            if order is None:
                return {
                    "found": False,
                    "order_id": order_id,
                    "message": (
                        f"Order {order_id} was not found "
                        "in the company database."
                    ),
                }

            customer_id = order.get("customer_id")
            customer = (
                get_customer(customer_id)
                if customer_id
                else None
            )

            return {
                "found": True,
                "order": order,
                "customer": customer,
            }

        if tool_name == "check_refund_eligibility":
            order_id = str(tool_input.get("order_id", "")).strip()

            if not order_id:
                return {
                    "found": False,
                    "eligible": False,
                    "error": "The order_id parameter is required.",
                }

            return check_refund_eligibility(order_id)

        if tool_name == "search_knowledge_base":
            query = str(tool_input.get("query", "")).strip()

            if not query:
                return {
                    "found": False,
                    "results": [],
                    "error": "The query parameter is required.",
                }

            knowledge_result = search_knowledge_base(
                query=query,
                number_of_results=3,
            )

            return {
                "found": knowledge_result.get("found", False),
                "query": knowledge_result.get("query", query),
                "results": [
                    {
                        "text": item.get("text", ""),
                        "source": item.get("source"),
                        "score": item.get("score"),
                        "document": self._extract_document_name(
                            item.get("source")
                        ),
                    }
                    for item in knowledge_result.get("results", [])
                ],
            }

        return {
            "found": False,
            "error": f"Unknown tool: {tool_name}",
        }

    @staticmethod
    def _extract_document_name(
        source: str | None,
    ) -> str | None:
        if not source:
            return None

        return source.rstrip("/").split("/")[-1]

    @staticmethod
    def _extract_text(
        content: list[dict[str, Any]],
    ) -> str:
        text = "".join(
            block.get("text", "")
            for block in content
            if "text" in block
        )

        text = re.sub(
            r"<thinking>.*?</thinking>",
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        return text.strip()

    @staticmethod
    def _extract_metrics(
        response: dict[str, Any],
    ) -> tuple[int, int, int]:
        usage = response.get("usage", {})
        metrics = response.get("metrics", {})

        return (
            usage.get("inputTokens", 0),
            usage.get("outputTokens", 0),
            metrics.get("latencyMs", 0),
        )

    def chat(self, message: str) -> dict[str, Any]:
        cleaned_message = message.strip()

        if not cleaned_message:
            raise ValueError("The message cannot be empty.")

        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [{"text": cleaned_message}],
            }
        ]

        total_input_tokens = 0
        total_output_tokens = 0
        total_latency_ms = 0
        max_tool_iterations = 5

        try:
            for _ in range(max_tool_iterations):
                response = self._call_model(messages)

                input_tokens, output_tokens, latency_ms = (
                    self._extract_metrics(response)
                )

                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
                total_latency_ms += latency_ms

                assistant_message = response["output"]["message"]
                messages.append(assistant_message)

                if response.get("stopReason") != "tool_use":
                    answer = self._extract_text(
                        assistant_message.get("content", [])
                    )

                    if not answer:
                        answer = (
                            "I could not generate a valid response. "
                            "Please try again."
                        )

                    return {
                        "answer": answer,
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                        "latency_ms": total_latency_ms,
                    }

                tool_results: list[dict[str, Any]] = []

                for content_block in assistant_message.get(
                    "content",
                    [],
                ):
                    tool_use = content_block.get("toolUse")

                    if tool_use is None:
                        continue

                    tool_use_id = tool_use["toolUseId"]
                    tool_name = tool_use["name"]
                    tool_input = tool_use.get("input", {})

                    result = self._execute_tool(
                        tool_name=tool_name,
                        tool_input=tool_input,
                    )

                    tool_results.append(
                        {
                            "toolResult": {
                                "toolUseId": tool_use_id,
                                "content": [{"json": result}],
                                "status": (
                                    "error"
                                    if result.get("error")
                                    else "success"
                                ),
                            }
                        }
                    )

                if not tool_results:
                    raise RuntimeError(
                        "Bedrock requested a tool, but no valid "
                        "tool call was received."
                    )

                messages.append(
                    {
                        "role": "user",
                        "content": tool_results,
                    }
                )

            raise RuntimeError(
                "The maximum number of tool calls was reached."
            )

        except ClientError as exc:
            error = exc.response.get("Error", {})

            raise RuntimeError(
                f"{error.get('Code', 'BedrockError')}: "
                f"{error.get('Message', 'Bedrock request failed.')}"
            ) from exc

        except BotoCoreError as exc:
            raise RuntimeError(
                "Unable to communicate with Amazon Bedrock."
            ) from exc

        except KeyError as exc:
            raise RuntimeError(
                f"Invalid Bedrock response: missing field {exc}."
            ) from exc