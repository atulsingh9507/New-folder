from fastapi import FastAPI, HTTPException, Depends, Request, Form, UploadFile, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import uvicorn
from passlib.context import CryptContext

from database import SessionLocal, engine
from models import User, JobApplication
from schemas import JobApplicationCreate
from utils import save_file

app = FastAPI()

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password hashing (keep this as it is)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Routes (keep all route definitions as they are)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup/", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse("signup_form.html", {"request": request})

@app.post("/signup/", response_class=HTMLResponse)
async def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    firstName: str = Form(...),
    lastName: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    hashed_password = pwd_context.hash(password)
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(
        username=username,
        hashed_password=hashed_password,
        firstName=firstName,
        lastName=lastName,
        phone=phone,
        email=email
    )
    db.add(new_user)
    db.commit()
    return templates.TemplateResponse("signup_success.html", {"request": request, "username": username})

@app.get("/login/", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login_form.html", {"request": request})

@app.post("/login/", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse("login_form.html", {"request": request, "error_message": "Invalid username or password"})
    
    response = RedirectResponse(url="/job_application_form/", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))
    return response

@app.get("/job_application_form/", response_class=HTMLResponse)
async def job_application_form(request: Request, user_id: int = Cookie(None), db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    existing_application = db.query(JobApplication).filter(JobApplication.user_id == user_id).first()

    if existing_application:
        return templates.TemplateResponse("display_application.html", {"request": request, "application": existing_application})
    else:
        return templates.TemplateResponse("job_application_form.html", {"request": request})

@app.post("/submit_application/", response_class=HTMLResponse)
async def submit_application(
    request: Request,
    job_application: JobApplicationCreate,
    user_id: int = Cookie(None),
    db: Session = Depends(get_db)
):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    existing_application = db.query(JobApplication).filter(JobApplication.user_id == user_id).first()
    if existing_application:
        return templates.TemplateResponse("application_already_submitted.html", {"request": request})

    resume_path = save_file(job_application.upload_file)
    photo_path = save_file(job_application.photo) if job_application.photo else None

    new_application = JobApplication(**job_application.dict(), user_id=user_id, upload_file=resume_path, photo=photo_path)
    db.add(new_application)
    db.commit()

    return templates.TemplateResponse("application_success.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
