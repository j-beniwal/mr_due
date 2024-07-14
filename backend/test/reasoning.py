from dotenv import load_dotenv
load_dotenv()

from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.ollama import Ollama 
from llama_index.core import Settings, get_response_synthesizer
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.postprocessor import KeywordNodePostprocessor

from enum import Enum
from typing import List
from pydantic import Field
from llama_index.core.bridge.pydantic import BaseModel
def store_index_locally(index, persist_dir):
    index.storage_context.persist(persist_dir=persist_dir)
    return

def restore_index_from_local(persist_dir:str):
    storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
    index = load_index_from_storage(storage_context)
    return index

# def store_index_to_chroma(collection_name="llama"):
#     # Note: Lazy import
#     import chromadb
#     from llama_index.vector_stores.chroma import ChromaVectorStore
    
#     db = chromadb.PersistentClient(path="./chroma_db")
#     chroma_collection = db.get_or_create_collection(collection_name)
    
#     # assign chroma as the vector_store to the context
#     vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
#     storage_context = StorageContext.from_defaults(vector_store=vector_store)

#     return storage_context

def add_new_documents_to_index(index, new_documents):
    # index = VectorStoreIndex([])
    for doc in documents:
        index.insert(doc)
    return index


# Models

class ComplianceStatus(str, Enum):
    COMPLIANT = "True"
    NOT_COMPLIANT = "False"
    AMBIGUOUS = "Ambiguous"

class ComplianceAnalysis(BaseModel):
    """
    Represents the result of a compliance analysis for a specific requirement.

    Attributes:
        is_compliant (bool): Indicates whether the requirement is met based on the evidence.
            True if the requirement is fully satisfied, False otherwise.

        reason (str): A detailed explanation of the compliance status.
            This should include references to specific evidence and justify the compliance decision.

        confidence (float): The level of confidence in the analysis, ranging from 0 to 1.
            0 represents no confidence, 1 represents absolute certainty.
            This score should reflect the analyst's certainty based on the available evidence.
    """

    is_compliant: bool
    reason: str
    confidence: float
    # references: str



## model initilization
Settings.llm = OpenAI(temperature=0.1, model="gpt-4o")
# Settings.llm = Ollama(model="llama2", request_timeout=60.0)
text_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=10)
Settings.text_splitter = text_splitter
Settings.embed_model = OpenAIEmbedding()
# Settings.embed_model = OpenAIEmbedding(embed_batch_size=42)

## data loading
documents = SimpleDirectoryReader("data").load_data()
# print(documents) # list of Document objects each having id, ebedding, metadata{file_path, file_name, file_type ...}, text
# in our case it has two object example_checklist and example_text

## Transform the data
# create vector index only for the evidence documents
evidence_documents = [document for document in documents if document.metadata["file_name"] == "example_report.txt"]

## load data from loacl
storage_context = StorageContext.from_defaults(persist_dir="./index")
evidence_index = load_index_from_storage(storage_context)

# ## Index and store the data
# evidence_index = VectorStoreIndex.from_documents(
#     evidence_documents, 
#     # transformations=[text_splitter, Settings.llm],
#     # storage_context= store_index_to_chroma(collection_name="llama")
# )

## store the data to stop making the index again and again
store_index_locally(evidence_index, persist_dir="./index")

## query the data 
# simplest for of query engine
query_engine = evidence_index.as_query_engine( output_cls=ComplianceAnalysis, response_mode="compact")

requirement = "Clear procedures are in place to detect, report, and investigate personal data breaches within the required 10-hour timeframe."
prompt = f"""
    As an expert compliance analyst with extensive experience in due diligence, 
    evaluate if the following compliance requirement is met based on the provided evidence:

    Requirement: {requirement}

    Analyze the evidence thoroughly and consider:
    1. Explicit mentions of this requirement
    2. Full satisfaction of the requirement if mentioned
    3. Indirect evidence suggesting compliance
    4. Any discrepancies or areas of concern

    Provide your assessment using the ComplianceAnalysis structure:
    - is_compliant: boolean indicating if the requirement is met
    - reason: detailed explanation referencing specific evidence
    - confidence: float from 0 to 1 indicating your certainty

    Ensure your explanation is clear, concise, and well-supported by the evidence.
    """ 
response = query_engine.query(prompt)

print(response.is_compliant)
print(response.reason)
print(response.confidence)

# # configure retriever
# retriever = VectorIndexRetriever(
#     index=evidence_index,
#     similarity_top_k=10,
# )

# # node postprocessors
# node_postprocessors = [
#     # KeywordNodePostprocessor(
#     #     required_keywords=["Combinator"], exclude_keywords=["Italy"]
#     # ),
#     SimilarityPostprocessor(similarity_cutoff=0.7)
# ]

# # configure response synthesizer
# response_synthesizer = get_response_synthesizer()

# # assemble query engine
# query_engine = RetrieverQueryEngine(
#     retriever=retriever,
#     response_synthesizer=response_synthesizer,
#     node_postprocessors=node_postprocessors
# )

# # query
# response = query_engine.query("regular audits should be done, what is the frequency of audits?")
# print(response)

