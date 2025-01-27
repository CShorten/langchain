"""Wrapper around weaviate vector database."""
from __future__ import annotations

from typing import Any, Iterable, List, Optional

from langchain.docstore.document import Document
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.base import VectorStore

from weaviate.util import get_valid_uuid
from uuid import uuid4


class Weaviate(VectorStore):
    """Wrapper around Weaviate vector database.

    To use, you should have the ``weaviate-client`` python package installed.

    Example:
        .. code-block:: python

            import weaviate
            from langchain.vectorstores import Weaviate
            client = weaviate.Client(url=os.environ["WEAVIATE_URL"], ...)
            weaviate = Weaviate(client, index_name, text_key)

    """

    def __init__(
        self,
        client: Any,
        index_name: str,
        text_key: str,
        attributes: Optional[List[str]] = None,
    ):
        """Initialize with Weaviate client."""
        try:
            import weaviate
        except ImportError:
            raise ValueError(
                "Could not import weaviate python package. "
                "Please it install it with `pip install weaviate-client`."
            )
        if not isinstance(client, weaviate.Client):
            raise ValueError(
                f"client should be an instance of weaviate.Client, got {type(client)}"
            )
        self._client = client
        self._index_name = index_name
        self._text_key = text_key
        self._query_attrs = [self._text_key]
        if attributes is not None:
            self._query_attrs.extend(attributes)



    def add_texts(
        self, texts: Iterable[str], metadatas: Optional[List[dict]] = None
    ) -> List[str]:
        """Upload texts with metadata (properties) to Weaviate."""
        self._client.batch.configure(
        batch_size=16,
        dynamic=True,
        timeout_retries=3,
        callback=None,
        )

        for doc in texts:
            data_properties = {
                self._text_key: doc[self._text_key],
            }
            for key in metadatas.keys():
                data_properties[key] = metadatas[key]

            id = get_valid_uuid(uuid4())
            self._client.batch.add_data_object(data_properties, self._index_name, id)
        
        print("Texts successfully imported to Weaviate.")


    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Look up similar documents in weaviate."""
        content = {"concepts": [query]}
        query_obj = self._client.query.get(self._index_name, self._query_attrs)
        result = query_obj.with_near_text(content).with_limit(k).do()
        docs = []
        for res in result["data"]["Get"][self._index_name]:
            text = res.pop(self._text_key)
            docs.append(Document(page_content=text, metadata=res))
        return docs

    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> VectorStore:
        """Not implemented for Weaviate yet."""
        raise NotImplementedError("weaviate does not currently support `from_texts`.")
