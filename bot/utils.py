from typing import Any, Dict
import uuid
import aiohttp
import config
class RetrievalUtils:
    def __init__(self, config):
        self.config = config

    def _apply_input_prompt_template(self, question: str, chat_mode="assistant") -> str:
            """
                A helper function that applies additional template on user's question.
                Prompt engineering could be done here to improve the result.
            """
            if chat_mode not in config.chat_modes.keys():
                raise ValueError(f"Chat mode {chat_mode} is not supported")
            prompt_template = config.chat_modes[chat_mode]["prompt_template"]
            prompt_template = prompt_template.replace("{question}", question)
            prompt_template += "\n\n"

            return prompt_template

    async def query(self, query_prompt: str, top_similarity=5) -> Dict[str, Any]:
            """
            Query vector database to retrieve chunk with user's input questions.
            """
            url = "https://chatvector.fly.dev/query"
            headers = {
                "Content-Type": "application/json",
                "accept": "application/json",
                "Authorization": f"Bearer {self.config.retrieval_plugin_bearer_token}",
            }
            data = {"queries": [{"query": query_prompt, "top_k": top_similarity}]}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        raise ValueError(f"Error: {response.status} : {await response.text()}")

    async def upsert(self, content: str, file_name: str = None, file_title: str = None, file_id: str = None, author: str = None):
        """
        Upload one piece of text to the database.
        """
        url = "https://chatvector.fly.dev/upsert"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.retrieval_plugin_bearer_token}",
        }

        data = {
            "documents": [{
                "id": file_id or str(uuid.uuid4()),
                "text": content,
                "metadata": {
                    "url": file_name or "unknown",
                    "author": author or "anonymous",
                }
            }]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers, timeout=600) as response:
                msg = ""
                if response.status == 200:
                    msg = "Content uploaded successfully."
                else:
                    msg = f"Error: {response.status} : {await response.text()}"
                return msg
