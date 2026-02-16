from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="银航宝·深蓝启航")

# 挂载静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class AuthPayload(BaseModel):
    username: str
    password: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 示例登录API
@app.post("/api/login")
async def login(payload: AuthPayload):
    # 此处应接入真实认证逻辑
    if payload.username and payload.password:
        return JSONResponse({"success": True, "msg": "登录成功（演示）"})
    return JSONResponse({"success": False, "msg": "账号或密码错误"})

# 示例注册API
@app.post("/api/register")
async def register(payload: AuthPayload):
    if not payload.username or not payload.password:
        return JSONResponse({"success": False, "msg": "账号或密码不能为空"})
    # 演示返回
    return JSONResponse({"success": True, "msg": "注册成功（演示）"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
