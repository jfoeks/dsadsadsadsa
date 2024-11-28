from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, Client
import bcrypt

# Инициализация базы данных
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Зависимость для подключения к базе данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/menu", response_class=HTMLResponse)
async def menu(request: Request):
    menu_items = [
        {"name": "Бургер", "price": "200 ₽"},
        {"name": "Пицца", "price": "500 ₽"},
        {"name": "Салат", "price": "300 ₽"},
    ]
    return templates.TemplateResponse("menu.html", {"request": request, "menu_items": menu_items})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    client = Client(email=email, hashed_password=hashed_password.decode("utf-8"))
    try:
        db.add(client)
        db.commit()
        return RedirectResponse("/", status_code=303)
    except:
        error_message={
            "message":'Такой пользователь уже существует'
        }
        return templates.TemplateResponse("register.html", {"request": request,'error_message':error_message})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Ищем пользователя по email
    client = db.query(Client).filter(Client.email == email).first()

    # Если пользователь не найден или пароль неверный
    if not client or not bcrypt.checkpw(password.encode("utf-8"), client.hashed_password.encode("utf-8")):
        error_message = "Логин или пароль неверны"
        return templates.TemplateResponse(
            "login.html", {"request": request, "error_message": error_message}
        )

    # Если логин успешен, сохраняем информацию о пользователе в cookie
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="user_email", value=email, httponly=True)  # Устанавливаем cookie с email
    return response
@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("user_email")  # Удаляем cookie
    return response