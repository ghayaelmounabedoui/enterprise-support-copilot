from typing import Any
import re
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.services.refund_service import check_refund_eligibility
from app.core.config import get_settings
from app.services.order_service import get_order
from app.services.customer_service import get_customer

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
            "Use get_order when the user asks only about an order. "
            "Use get_customer when the user asks directly about a customer. "
            "Use get_order_with_customer when the user asks who is associated "
            "with an order or requests both order and customer information. "
            "Never invent company data. "
            "Only use information returned by the tools."
            "Use check_refund_eligibility whenever the user asks whether "
            "an order can be refunded or returned. "
            "Never decide refund eligibility yourself. "
            "Always use the business tool for refund decisions. "
        )
    }
]
        
        self.tool_config = {
            "tools": [
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
                }
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
            order_id = tool_input.get("order_id")

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
        if tool_name == "get_order_with_customer":
            order_id = tool_input.get("order_id")

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
            customer = get_customer(customer_id) if customer_id else None

            return {
                "found": True,
                "order": order,
                "customer": customer,
            }
        if tool_name == "check_refund_eligibility":
            order_id = tool_input.get("order_id")

            if not order_id:
                return {
                    "found": False,
                    "eligible": False,
                    "error": "The order_id parameter is required.",
                }

            return check_refund_eligibility(order_id)
        return {
            "found": False,
            "error": f"Unknown tool: {tool_name}",
        }

    @staticmethod
    def _extract_text(
        content: list[dict[str, Any]],
    ) -> str:
        text = "".join(
            block.get("text", "")
            for block in content
            if "text" in block
        )

        # Supprime les blocs <thinking>...</thinking>
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
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [{"text": message}],
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
                    return {
                        "answer": self._extract_text(
                            assistant_message["content"]
                        ),
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                        "latency_ms": total_latency_ms,
                    }

                tool_results: list[dict[str, Any]] = []

                for content_block in assistant_message["content"]:
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
                                    if "error" in result
                                    else "success"
                                ),
                            }
                        }
                    )

                if not tool_results:
                    raise RuntimeError(
                        "Bedrock a demandé un outil, "
                        "mais aucun appel valide n’a été reçu."
                    )

                messages.append(
                    {
                        "role": "user",
                        "content": tool_results,
                    }
                )

            raise RuntimeError(
                "Nombre maximal d’appels d’outils atteint."
            )

        except ClientError as exc:
            error = exc.response.get("Error", {})

            raise RuntimeError(
                f"{error.get('Code', 'BedrockError')}: "
                f"{error.get('Message', 'Bedrock request failed.')}"
            ) from exc

        except BotoCoreError as exc:
            raise RuntimeError(
                "Impossible de communiquer avec Amazon Bedrock."
            ) from exc

        except KeyError as exc:
            raise RuntimeError(
                f"Réponse Bedrock invalide : champ manquant {exc}."
            ) from exc