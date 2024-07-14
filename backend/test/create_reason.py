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
from typing import List, Union, Dict, Literal

from llama_index.core.bridge.pydantic import BaseModel
def store_index_locally(index, persist_dir):
    index.storage_context.persist(persist_dir=persist_dir)
    return

def restore_index_from_local(persist_dir:str):
    storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
    index = load_index_from_storage(storage_context)
    return index

class ChecklistItem(BaseModel):
    """
    Represents an individual item in the compliance checklist.

    Attributes:
        id (int): The unique identifier for the checklist item.
        requirement (str): The specific compliance requirement being evaluated.
        is_compliant (str): The compliance status, which can be "True", "False", or "Ambiguous".
        reason (str): The explanation for the compliance status.
        references (str): Citations or references to documents used in the reasoning.
        metadata (Dict): Additional metadata related to the checklist item.
        confidence (float): The level of confidence in the analysis, ranging from 0 to 1.
    
    """
    id: int
    requirement: str
    is_compliant: Literal["True", "False", "Ambiguous"] = None
    reason: str
    references: str
    metadata: Dict = Field(default_factory=dict)
    confidence: float = None

class Checklist(BaseModel):
    """
    Represents the overall compliance checklist.

    Attributes:
        checklist (List[ChecklistItem]): A list of individual checklist items.
    """
    checklist: List[ChecklistItem]
    

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
    for doc in new_documents:
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

def get_compliance_updates(compliance_checklist: Checklist) -> Checklist:
    ## data loading
    documents = SimpleDirectoryReader("data").load_data()

    ## Transform the data
    evidence_documents = [document for document in documents if document.metadata["file_name"] == "example_report.txt"]

    # ## Index and store the data
    evidence_index = VectorStoreIndex.from_documents(
        evidence_documents
    )

    ## query the data 
    # simplest for of query engine
    query_engine = evidence_index.as_query_engine( output_cls=ComplianceAnalysis, response_mode="compact")

    for item in compliance_checklist.checklist:
        requirement = item.requirement
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
        
        item.is_compliant = response.is_compliant
        item.reason = response.reason
        item.references = response.references
        item.confidence = response.confidence

    # print(response.is_compliant)
    # print(response.reason)
    # print(response.confidence)
    
    return compliance_checklist


if __name__ == "__main__":
    compliance_checklist = Checklist(
        checklist=[
            ChecklistItem(
                id=1,
                requirement="Clear procedures are in place to detect, report, and investigate personal data breaches within the required 10-hour timeframe.",
                is_compliant=None,
                reason="",
                references="",
                metadata={}
            ),
            ChecklistItem(
                id=2,
                requirement="All employees have completed mandatory data privacy training within 30 days of hire.",
                is_compliant=None,
                reason="",
                references="",
                metadata={}
            ),
            ChecklistItem(
                id=3,
                requirement="Access to personal data is restricted to authorized personnel only.",
                is_compliant=None,
                reason="",
                references="",
                metadata={}
            )
        ]
    )

    updated_compliance_checklist = get_compliance_updates(compliance_checklist)

    print(updated_compliance_checklist)