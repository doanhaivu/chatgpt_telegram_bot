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
                Use the following pieces of context to answer the question at the end in Vietnamese. 
                If you don't know the answer, just say that you don't know, don't try to make up an answer. Answer the question only using the given context.
                Say explicitly if the question cannot be answered using the given text but only with your existing knowledge.
                Also state explicitly if there is a conflict between what you know already and what is stated in the given text.
            """
            prompt_vi = f"""
                Sử dụng các thông tin sau để trả lời câu hỏi ở cuối.
                Nếu bạn không biết câu trả lời, hãy nói rằng bạn không biết, đừng cố gắng bịa ra một câu trả lời. Chỉ trả lời câu hỏi dựa trên thông tin đã cho.
                Nói rõ ràng nếu câu hỏi không thể được trả lời dựa trên nội dung đã cho nhưng có thể nếu dựa trên kiến thức hiện tại của bạn.
                Cũng hãy nói rõ ràng nếu có sự mâu thuẫn giữa những gì bạn đã biết và những gì được nêu ra trong ngữ cảnh đã cho.
                Sử dụng tiếng Việt trong câu trả lời của bạn.
            """
            return prompt_vi

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
