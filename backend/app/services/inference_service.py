import os
from typing import List, Dict
import llama_index
from llama_index.core import GPTVectorStoreIndex, SimpleDirectoryReader, Document
from llama_index.core import PromptTemplate
# import chromadb
# from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI

from llama_index.core import StorageContext

from llama_index.llms.openai import OpenAI
import PyPDF2
import json
import hashlib

from dotenv import load_dotenv
load_dotenv()

class InferenceService:
    def __init__(self):
        self.checklist_engine = None
        self.evidence_engine = None
        self.llm = OpenAI(model="gpt-4")
        self.index = None
        
    def process_documents(self, checklist_files: List[str], evidence_files: List[str]):
        # Process checklist documents
        
        # checklist_docs = self._load_documents(checklist_files)
        # self.checklist_engine = GPTVectorStoreIndex.from_documents(checklist_docs)
        data = self._load_documents(checklist_files)
        index = VectorStoreIndex.from_documents(data)
        self.checklist_engine = index.as_chat_engine(chat_mode="best", llm=self.llm, verbose=True)
        # Process evidence documents
        
        # evidence_docs = self._load_documents(evidence_files)
        # self.evidence_engine = GPTVectorStoreIndex.from_documents(evidence_docs)
        data = self._load_documents(evidence_files)
        index = VectorStoreIndex.from_documents(data)
        self.evidence_engine = index.as_chat_engine(chat_mode="best", llm=self.llm, verbose=True)
        
    def _load_documents(self, file_paths: List[str]) -> List[Document]:
        documents = []
        for file_path in file_paths:
            if file_path.endswith('.pdf'):
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    documents.append(Document(text=text))
            elif file_path.endswith('.txt'):
                with open(file_path, 'r') as file:
                    text = file.read()
                documents.append(Document(text=text))
                # data = SimpleDirectoryReader(input_dir=file_path).load_data()
        print("documents: ", documents)
        return documents

    def generate_checklist_json(self) -> Dict:
        print("generate_checklist_json")
        if not self.checklist_engine:
            raise ValueError("Checklist documents have not been processed yet.")

        checklist_prompt = PromptTemplate(
            "Extract the compliance requirements from the following text and format them as a JSON array. "
            "Each item should have an 'id' (use a hash of the requirement), 'requirement' (the actual requirement text), "
            "and leave 'is_compliant', 'reason', 'references', and 'metadata' empty or null.\n\n"
            "Text: {text}\n\n"
            "JSON Output:"
        )

        prompt = checklist_prompt.format(text="Extract compliance requirements")
        response = self.checklist_engine.chat(prompt)
        print("response: ", response)
        # query_engine = self.checklist_engine.as_query_engine(text_qa_template=checklist_prompt)
        # response = query_engine.query("Extract compliance requirements")

        try:
            checklist_items = json.loads(response.response)
            return {"checklist": checklist_items}
        except json.JSONDecodeError:
            raise ValueError("Failed to parse the generated checklist JSON")

    def evaluate_compliance(self, checklist: Dict) -> Dict:
        if not self.evidence_engine:
            raise ValueError("Evidence documents have not been processed yet.")

        evaluation_prompt = PromptTemplate(
            "Based on the following requirement, determine if it is compliant according to the evidence documents. "
            "Provide a reason for your determination and any relevant references from the evidence.\n\n"
            "Requirement: {requirement}\n\n"
            "Response format:\n"
            "is_compliant: [True/False/Ambiguous]\n"
            "reason: [Your reasoning here]\n"
            "references: [Relevant references from evidence documents]"
        )

        # query_engine = self.evidence_engine.as_query_engine(text_qa_template=evaluation_prompt)

        for item in checklist['checklist']:
            # response = query_engine.query(item['requirement'])
            response = self.evidence_engine.chat(evaluation_prompt.format(requirement=item['requirement']))
            print("response in evaluate_compliance: ", response)
            try:
                eval_result = self._parse_evaluation_response(response.response)
                item.update(eval_result)
            except ValueError as e:
                print(f"Error processing requirement '{item['requirement']}': {str(e)}")
                item.update({
                    'is_compliant': 'Ambiguous',
                    'reason': 'Failed to evaluate compliance',
                    'references': ''
                })

        return checklist

    def _parse_evaluation_response(self, response: str) -> Dict:
        lines = response.strip().split('\n')
        result = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip().lower()] = value.strip()
        
        if 'is_compliant' not in result or 'reason' not in result or 'references' not in result:
            raise ValueError("Incomplete evaluation response")
        
        return result

inference_service = InferenceService()