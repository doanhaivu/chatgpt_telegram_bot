from typing import Any, Dict
import uuid
import aiohttp

class RetrievalUtils:
    def __init__(self, config):
        self.config = config

    def _apply_input_prompt_template(self, question: str) -> str:
            """
                A helper function that applies additional template on user's question.
                Prompt engineering could be done here to improve the result. Here I will just use a minimal example.
            """
            prompt = f"""
                Considering above input from me, answer the question: {question}.
                Use the input to formulate the answer to the best of your ability.
                If the input is not enough, or is not relevant, you can use your own words to answer the question but not exceed 200 words. Remember to end your answer with an approriate emoji.
                If the input is relavent and you don't need more information, you can add to the answer your own words if you think it's necessary, but not exceed 100 words. Remember to separate your answer from the input with an approriate emoji.
            """
            return prompt

    async def query(self, query_prompt: str) -> Dict[str, Any]:
            """
            Query vector database to retrieve chunk with user's input questions.
            """
            url = "https://chatvector.fly.dev/query"
            headers = {
                "Content-Type": "application/json",
                "accept": "application/json",
                "Authorization": f"Bearer {self.config.retrieval_plugin_bearer_token}",
            }
            data = {"queries": [{"query": query_prompt, "top_k": 5}]}

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
