from pydantic import BaseModel, EmailStr
from fastapi import UploadFile
from typing import Optional

class JobApplicationCreate(BaseModel):
    job_title: str
    job_description: str
    fullName: str
    phone: str
    email: EmailStr
    upload_file: UploadFile
    photo: Optional[UploadFile] = None
    address: str
    position: str
    gender: str
    qualification: str
    reference: Optional[str] = None
