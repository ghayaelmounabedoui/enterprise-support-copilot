from pprint import pprint

from app.services.knowledge_base_service import search_knowledge_base


result = search_knowledge_base(
    "How many days does a customer have to request a refund?"
)

pprint(result)