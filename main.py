import mysql.connector
from fastapi import FastAPI, Form, Request
from pydantic import BaseModel
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from typing import Optional
import logging


def get_db():  # 連接資料庫
    return mysql.connector.connect(
        user="root", password="1234", host="localhost", database="website"
    )


app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="your_secret_key")

# Mount static files (CSS, JS if needed)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 Templates
templates = Jinja2Templates(directory="templates")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/signin")
def signin(request: Request, username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        return RedirectResponse(url="/error?message=請輸入帳號密碼", status_code=303)
    con = get_db()
    cursor = con.cursor()
    cursor.execute(
        "SELECT username, password, id, name FROM member WHERE username = %s",
        (username,),
    )
    existing_user = cursor.fetchone()
    con.close()
    if existing_user is None:
        return RedirectResponse(
            url="/error?message=帳號不存在，請先完成註冊", status_code=303
        )
    if username == existing_user[0] and password == existing_user[1]:
        request.session["USER_ID"] = existing_user[2]
        request.session["SIGNED-IN"] = True
        request.session["NAME"] = existing_user[3]
        return RedirectResponse(url="/member", status_code=303)
    return RedirectResponse(url="/error?message=帳號或密碼輸入錯誤", status_code=303)


@app.post("/signup")
def signup(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
):
    # 檢查資料庫中是否已存在此用戶名
    con = get_db()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM member WHERE username = %s", (username,))
    existing_user = cursor.fetchone()
    con.close()
    if existing_user is not None:
        return RedirectResponse(url="/error?message=此帳號已存在", status_code=303)
    # 插入資料庫
    con = get_db()
    cursor = con.cursor()
    cursor.execute(
        "INSERT INTO member (name,username, password) VALUES (%s,%s, %s)",
        (name, username, password),
    )
    con.commit()
    con.close()
    return RedirectResponse(url="/", status_code=303)


@app.get("/member")
def member(request: Request):
    if request.session.get("SIGNED-IN"):
        user_id = request.session.get("USER_ID")
        name = request.session.get("NAME", "訪客")
        con = get_db()
        cursor = con.cursor(dictionary=True)
        messages = cursor.execute(
            "SELECT member_id, name, content, m.id as message_id FROM message m join member mem on m.member_id = mem.id",
        )
        messages = cursor.fetchall()
        con.close()
        return templates.TemplateResponse(
            "member.html",
            {
                "request": request,
                "user_id": user_id,
                "name": name,
                "messages": messages,
            },
        )
    return RedirectResponse(url="/")


@app.get("/api/member")
def get_member_messages(request: Request, username: Optional[str] = None):
    if request.session.get("SIGNED-IN"):
        try:
            con = get_db()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                "SELECT id as id, name, username  FROM member WHERE username = %s",
                (username,),
            )
            messages = cursor.fetchone()
            con.close()
            return JSONResponse(content={"data": messages})  # 回傳 JSON 資料
        except Exception as e:
            logging.error(f"API Error: {e}")
            return JSONResponse(content={"data": None}, status_code=500)  # 500錯誤碼
    return JSONResponse(content={"data": None})  # 未登入回傳None


class UpdateMember(BaseModel):
    name: str


@app.patch("/api/member")
def update_member(request: Request, request_data: UpdateMember):
    if request.session.get("SIGNED-IN"):
        try:
            name = request_data.name
            con = get_db()
            cursor = con.cursor(dictionary=True)
            cursor.execute(
                "UPDATE member SET name = %s WHERE id = %s",
                (name, request.session.get("USER_ID")),
            )
            con.commit()
            con.close()
            request.session["NAME"] = name
            return JSONResponse(content={"ok": True})  # 回傳 JSON 資料
        except Exception as e:
            logging.error(f"API Error: {e}")
            return JSONResponse(content={"error": True}, status_code=500)


@app.post("/createMessage")
def create_message(request: Request, message: str = Form(...)):
    if request.session.get("SIGNED-IN"):
        con = get_db()
        cursor = con.cursor()
        cursor.execute(
            "INSERT INTO message (member_id, content) VALUES (%s, %s)",
            (request.session["USER_ID"], message),
        )
        con.commit()
        con.close()
        return RedirectResponse(url="/member", status_code=303)
    return RedirectResponse(url="/")


@app.post("/deleteMessage")
def delete_message(request: Request, message_id: int = Form(...)):
    if request.session.get("SIGNED-IN"):
        con = get_db()
        cursor = con.cursor()
        cursor.execute("DELETE FROM message WHERE id = %s", (message_id,))
        con.commit()
        con.close()
        return RedirectResponse(url="/member", status_code=303)
    return RedirectResponse(url="/")


@app.get("/error")
def error_page(request: Request, message: str):
    return templates.TemplateResponse(
        "error.html", {"request": request, "header": "失敗頁面", "message": message}
    )


@app.get("/signout")
def signout(request: Request):
    request.session["SIGNED-IN"] = False
    return RedirectResponse(url="/")
