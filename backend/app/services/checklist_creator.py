
from dotenv import load_dotenv
load_dotenv()

from typing import List, Union, Dict, Literal, Optional
from llama_index.program.openai import OpenAIPydanticProgram
from pydantic import Field
# from llama_index.core.bridge.pydantic import BaseModel


prompt_template_str = """\
You are given the list of compliance requirements. \
Your job is to convert them in the pydantic model. \

The pydantic model has the following structure:\
- checklist: it is a list of ChecklistItem

Each checklist item has the following attributes:\
- id: int unique identifier for the checklist item\
- requirement: str specific compliance requirement being evaluated (You have to fill this field)\
- is_compliant: None (Leave this field empty this will be filled by the user)\
- reason: (Leave this field empty this will be filled by the user)\
- references: (Leave this field empty this will be filled by the user)\
- metadata: (Leave this field empty this will be filled by the user)\

Below is the provided data for you to convert in the pydantic model.\
data: {checklist_data}
"""

def get_compliance_checklist():
    print("in get_compliance_checklist")
    # Node : lazy import due to dependency issues. 
    from pydantic import BaseModel
    class ChecklistItem(BaseModel):
        """
        Represents an individual item in the compliance checklist.

        Attributes:
            id (int): The unique identifier for the checklist item.
            requirement (str): The specific compliance requirement being evaluated.
            is_compliant (Literal["True", "False", "Ambiguous"]): The compliance status.
            reason (Optional[str]): The explanation for the compliance status.
            references (Optional[str]): Citations or references to documents used in the reasoning.
            metadata (Dict): Additional metadata related to the checklist item.
            confidence (Optional[float]): The level of confidence in the analysis, ranging from 0 to 1.
        """
        _id: int
        requirement: str
        is_compliant: Optional[Literal["True", "False", "Ambiguous"]] = None
        reason: Optional[str]
        references: Optional[str]
        metadata: Dict = Field(default_factory=dict)
        confidence: Optional[float] = None

    class Checklist(BaseModel):
        """
        Represents the overall compliance checklist.

        Attributes:
            checklist (List[ChecklistItem]): A list of individual checklist items.
        """
        checklist: List[ChecklistItem]
    
    with open("./uploads/example_checklist.txt", "r") as file:
        data = file.read()
        
    program = OpenAIPydanticProgram.from_defaults(
        output_cls=Checklist, prompt_template_str=prompt_template_str
    )

    output = program(
        checklist_data=data
    )

    print("checklist generated: ", output)
    return output

    
if __name__ == "__main__":
    checklist = get_compliance_checklist()
    for item in checklist.checklist:
        print(item)