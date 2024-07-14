import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
project_root = os.path.dirname(script_dir)
# Add the project root to the Python path
sys.path.insert(0, project_root)

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.models.compliance import Compliance
except ImportError as e:
    print(f"Error: {e}")
    print("Please make sure you have installed all required dependencies.")
    print("Run 'pip install motor' and ensure you have the latest version of pydantic installed.")
    print(f"Also, make sure you're running this script from the project root directory.")
    print(f"Current directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    sys.exit(1)

MONGO_URL = os.getenv("MONGODB_URL")
DB_NAME = os.getenv("DATABASE_NAME")

compliances = [
    "Health Insurance Portability and Accountability Act (HIPAA)",
    "Federal Trade Commission (FTC) Regulations",
    "General Data Protection Regulation (GDPR)",
    "Health Information Technology for Economic and Clinical Health Act (HITECH)",
    "Food and Drug Administration (FDA) Regulations",
    "Clinical Laboratory Improvement Amendments (CLIA)",
    "Occupational Safety and Health Administration (OSHA) Standards",
    "Centers for Medicare and Medicaid Services (CMS)",
    "Anti-Kickback Statute (AKS) and Stark Law",
    "Patient Safety and Quality Improvement Act (PSQIA)",
    "Electronic Health Record (EHR) Compliance"
]

async def init_db():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    for compliance_name in compliances:
        compliance = Compliance(
            name=compliance_name,
            metadata={},  # You can add more detailed metadata later
            document_paths=[],  # Add document paths as needed
            checklist=["Sample checklist item 1", "Sample checklist item 2"]  # Add real checklist items later
        )
        await db.compliances.insert_one(compliance.dict(by_alias=True))
    
    print("Compliance database initialized successfully!")

if __name__ == "__main__":
    try:
        asyncio.run(init_db())
    except Exception as e:
        print(f"An error occurred while initializing the database: {e}")
        sys.exit(1)