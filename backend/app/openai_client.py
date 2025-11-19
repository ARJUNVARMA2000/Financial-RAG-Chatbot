from __future__ import annotations

from typing import Iterable, List, Optional

from openai import OpenAI


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        chat_model: str = "gpt-4.1-mini",
        embedding_model: str = "text-embedding-3-large",
    ) -> None:
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self._client = OpenAI(**client_kwargs)
        self.chat_model = chat_model
        self.embedding_model = embedding_model

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        texts_list = list(texts)
        if not texts_list:
            return []
        response = self._client.embeddings.create(
            model=self.embedding_model,
            input=texts_list,
        )
        return [item.embedding for item in response.data]

    def chat(self, system_prompt: str, user_message: str) -> str:
        response = self._client.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""



