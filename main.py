

import os
import itertools
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, field_validator
import httpx
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from passlib.context import CryptContext
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
STREAMING_API_URL = 'https://api.heygen.com/v1/streaming.create_token'


API_KEY_5 = 'Zjk4ZjQwOWVkM2ExNDk5Y2FkMTU1NTI3MzA2NDgwMWEtMTcyMTY5NzI1OQ=='
API_KEY_6 = 'ZDRiN2QwYTRkM2U0NDEzNmIzY2U1MThhOGZhZjQ0MTYtMTcyMTk4MzU5OQ=='
API_KEY_7 = 'M2U5NTI1NWM3NzZlNDA3MGI4NjY0YzcxYmVkZTM1OWYtMTcyMTk4NDAxMw=='
API_KEY_8 = 'NzdlOTljYWI0ZjgyNGEwNDk5NzJkZWZlM2QwNTM1YTgtMTcyMTk4NDIyNA=='
API_KEY_9 = 'MDRkNjJjNTM1NmNiNGEwNDlkZWEwOWZkYTA1NTRkMTYtMTcyMTk4NDQxNg=='
API_KEY_10 = 'MWQ3M2ZjZGFkNDliNDZmYTg4Mzk1ODVjMzRjODNkOTAtMTcyMTk4NDY2NQ=='
API_KEY_12 = "N2FhNzRkZjVhZGI2NDM5ZTk5MDhkYTBiNGQ5OWI2NmUtMTcyMTk4NjM1NQ=="
API_KEY_13 = "ZjM3ZTdjZWRkMDE0NGUzMTkxNDgyMmM5YjNhYzhhNDEtMTcyMTk4NjI5Ng=="
API_KEY_14 = "MTJlOTAyMGFjYWZkNDdlNjg2M2JkYmE1ZGMwZTMzM2YtMTcyMTk4NTk2MQ=="
API_KEY_15 = "ZGYzMjc1ZTE5MjQ4NDE1ZmI2NDU4ZjhiYTcxNmNhMGYtMTcyMTk4NjE5OA=="
API_KEY_16 = 'NGViMDg3OTZkZDUzNDYzY2FhMjQ5MjhkYjcxMzVkYjgtMTcyMjEyNDMwMQ=='
API_KEY_17 ='ZTdiNzIwMTFmM2UwNDM5ZDkwMjA4YjAyM2NjZTA5MmQtMTcyMjE4NjQyMA=='
API_KEY_18 = 'M2Y3NTQxMTViMjkyNDg0M2IzZTkxNTM4Y2U4M2E3ZjAtMTcyMjE4NjYyOA=='
API_KEY_19 = 'MGFkNjdkNWIwOGFiNGViZWI4ZTMwNWY3NDIxMGUxZWYtMTcyMjE5MTQ4NA=='
API_KEY_20 = 'N2NhYzhhZGU1MTFiNDczYmIwMGNiM2FhMTIzZGUzNDMtMTcyMjE5MTU5Ng=='
API_KEY_21 = 'YmYyOWFkMTk3MjQxNDkzZmFlNjVkZWMwYmFmNTA1NjUtMTcyMjE5MTczNg=='
API_KEY_22 = 'M2I3YjVlZDhhZTgyNGY1Njg0MzRhNTZhZGFhNGJjY2UtMTcyMjE5MTkxMg=='
API_KEY_23 = 'MTU0OWJhMzQyNTczNDM5YWEyYmFiYjFmNDNjNjY2ZmUtMTcyMjE5NDA4MQ=='
API_KEY_24 = 'MmYxNTJjZTkxYjcxNDE0MTg5M2IwYWI1ZTRmNTU5NjktMTcyMjE5NDIwMQ=='
API_KEY_25 = 'MTY5OWQ1MWE0YTRhNDg2YTkxNWM3MjgwODFlMjE1NDgtMTcyMjE5NDM2Nw=='
API_KEY_26 = 'MWM4MzhlZDk0NWRkNDYwZWJiYjRmNWMyNDk3YTdiZDEtMTcyMjE5NDU0Mw=='



API_KEYS = [

    API_KEY_5,
    API_KEY_6,
    API_KEY_7,
    API_KEY_8,
    API_KEY_9,
    API_KEY_10,
    API_KEY_12,
    API_KEY_13,
    API_KEY_14,
    API_KEY_15,
    API_KEY_16,
    API_KEY_17,
    API_KEY_18,
    API_KEY_19,
    API_KEY_20,
    API_KEY_21,
    API_KEY_22,
    API_KEY_23,
    API_KEY_24,
    API_KEY_25,
    API_KEY_26
    
]

api_key_iterator = itertools.cycle(API_KEYS)

def get_next_api_key():
    return next(api_key_iterator)

# Initialize FastAPI
app = FastAPI()
print(os.getenv("DB_URL"))
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB client
dbu = 'mongodb://localhost:27017/'
client = AsyncIOMotorClient(os.getenv("DB_URL"))
db = client.mocktalk
sessions_collection = db.sessions
users_collection = db.users

# Security and authentication
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def decode_jwt(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token if decoded_token["exp"] >= time.time() else {}
    except:
        return {}

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if credentials.scheme != "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        try:
            payload = decode_jwt(jwtoken)
            return bool(payload)
        except:
            return False

class User(BaseModel):
    name: str
    email: EmailStr
    job_title: str
    experience: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None

class UserInDB(User):
    hashed_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# Initialize JWTBearer
jwt_bearer = JWTBearer()


# Initialize the OpenAI LLM model
model = ChatOpenAI(
    model="gpt-4o",
    max_retries=2,
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7,
)


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def get_user(email: str) -> Optional[dict]:
    user = await users_collection.find_one({"email": email})
    return user

async def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = await get_user(email)
    if not user or not verify_password(password, user.get("hashed_password")):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def save_cv(file: UploadFile, user_id: str) -> str:
    try:
        file_path = f"cvs/{user_id}_{file.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving CV: {e}")

@app.get('/resume/{user_id}', responses={
    200: {
        "content": {
            "application/pdf": {
                "schema": {
                    "type": "string",
                    "format": "binary"
                }
            }
        },
        "description": "PDF Resume file"
    },
    404: {
        "description": "User or CV not found"
    }
})
async def get_resume(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if "cv_path" not in user:
        raise HTTPException(status_code=404, detail="CV not found")
    cv_path = user.get("cv_path")
    return FileResponse(cv_path, media_type="application/pdf", filename="resume.pdf")

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    def validate_password(cls,v):
        if len(v) < 6:
            raise ValueError('Password must be at least 8 characters')
        return v

@app.post("/register")
async def register(
    register_request: RegisterRequest
):
    existing_user = await users_collection.find_one({"email": register_request.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered")
    user_dict = {
        "email": register_request.email,
        "hashed_password": get_password_hash(register_request.password),
        "_id": str(ObjectId())
    }
    result = await users_collection.insert_one(user_dict)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Registration failed")
    access_token = create_access_token(data={"sub": user_dict.get("email"), "_id": user_dict.get("_id")})
    return {"token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(token: dict = Depends(jwt_bearer)):
    decoded_token = decode_jwt(token)
    user = await users_collection.find_one({"_id":decoded_token.get("_id")})
    return user




@app.get("/feedbacks/me")
async def get_my_feedbacks(token: dict = Depends(jwt_bearer)):
    decoded_token = decode_jwt(token)
    feedbacks = await sessions_collection.find({"user_id": decoded_token.get("_id")}).to_list(length=100)
    return feedbacks


@app.post("/token")
async def login_for_access_token(login_data: LoginRequest):
    user = await authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.get("email"), "name":user.get("name"),"_id": str(user.get("_id"))})
    print(user)
    return {"token": access_token, "token_type": "bearer"}

store = {}

def get_session_history(session_id: str, position:str = None ,grade:str=None) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
        system_prompt = f"""
        <<ТВОИ ОТВЕТЫ НЕ ДОЛЖНЫ ПРЕВЫШАТЬ ЛИМИТ В 200 СИМВОЛОВ!!!>> - ОЧЕНЬ ВАЖНО

        Вы - топовый Software Engineer ИИ-интервьюер на MockTalk.ai, моделирующий реальные сценарии собеседований для различных позиций (Backend, Frontend, FullStack, Android dev, IOS dev, DS, ML, Data Engineer, Data Analytics, Cybersecurity и т.д.), а также для различных грейдов (INTERN, JUNIOR, MIDDLE, SENIOR).
        Все, что вы делаете на собеседовании, должно строго относиться к теме собеседования и не выходить за его пределы. 
        Будьте максимально краткими, без лишних слов, чтобы собеседование было продуктивным. 

        НАЧИНАЙ ВСЕГДА С ПРОСТЫХ ВОПРОСОВ, ПОСЛЕДОВАТЕЛЬНО ПЕРЕХОДИ К СЛОЖНЫМ и ПОТОМ ДАЛЬШЕ УГЛУБЛЯЙСЯ В ТЕМУ.

        САМОЕ ГЛАВНОЕ - задавайте вопросы и давайте ответы без лишних слов и будьте краткими, только по теме собеседования.

        ЗАДАВАЙТЕ ВОПРОСЫ ПОСЛЕДОВАТЕЛЬНО, ПО ОДНОМУ, чтобы пользователю было удобно отвечать.

        Когда пользователь просит объяснить какую-то тему или технологию, объясняйте кратко, просто и понятно.

        Если ответ пользователя недостаточно полный, задайте уточняющий вопрос по теме или предоставьте конкретные замечания о том, что было упущено.

        Проведите собеседование для кандидата на позицию {position} на грейд {grade}. 
        
        Задавайте сложные вопросы, требующие глубокого понимания и знаний конкретных технологий или специализаций. 
        Избегайте обычных вопросов, фокусируйтесь на более трудных задачах, которые редко задают на реальных собеседованиях.

        Избегайте частого перехода с одной темы на другую, обеспечьте логичное и последовательное развитие вопросов.

        В случаях с задачами на алгоритмы, если пользователь использует встроенные методы для решения задачи, попросите его решить задачу алгоритмически, без использования встроенных готовых методов.

        Ответы не должны превышать 3-4 предложений/200 символов.
        <<ТВОИ ОТВЕТЫ НЕ ДОЛЖНЫ ПРЕВЫШАТЬ ЛИМИТ В 200 СИМВОЛОВ!!!>> - ОЧЕНЬ ВАЖНО
        
        Будьте строгим и объективным в оценке кандидата. Если юзер не раскрыл тему, скажи чтобы он был детальным и конкретным.

        <<ТВОИ ОТВЕТЫ НЕ ДОЛЖНЫ ПРЕВЫШАТЬ ЛИМИТ В 200 СИМВОЛОВ!!!>> - ОЧЕНЬ ВАЖНО
        """


        store[session_id].add_message(SystemMessage(content=system_prompt))
    return store[session_id]


with_message_history = RunnableWithMessageHistory(model, get_session_history)

class InterviewSetting(BaseModel):
    company_name: str
    interview_type:str
    stack: str
    interview_date: str

class MessageRequest(BaseModel):
    session_id: str
    message: Optional[str] = None
    position:Optional[str] = None
    grade:Optional[str] = None
    type:Optional[str] = None

@app.post('/get-access-token')
async def get_access_token():
    try:
        async with httpx.AsyncClient() as client:
            x_api_key = get_next_api_key()
            print(x_api_key, "x_api_key")
            headers = {
                'x-api-key': x_api_key,
                'Content-Type': 'application/json'
            }
            response = await client.post(STREAMING_API_URL, headers=headers)
            response.raise_for_status()
            data = response.json()
            token = data.get('data', {}).get('token')
            return {"token": token}
    except httpx.HTTPStatusError as http_error:
        raise HTTPException(status_code=http_error.response.status_code, detail='Failed to retrieve access token')
    except httpx.RequestError as request_error:
        raise HTTPException(status_code=500, detail='Network error')

@app.post('/chat')
async def chat_with_history(request: MessageRequest):
    try:
        session_id = request.session_id
        user_message = request.message
        position = request.position
        grade = request.grade
        type = request.type
        final_message = "Вот мой код для вопроса по кодингу, проверь соответсует ли решение твоему вопросу :  " + user_message if type == "code" else user_message
        session_history =  get_session_history(session_id,position,grade)
        session_history.add_message(HumanMessage(content=final_message))


        config = {"configurable": {"session_id": session_id}}
        response = with_message_history.invoke(
            [HumanMessage(content=final_message)],
            config=config,
        )

        return {"response": response.content}
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Internal server error: {error}")


@app.post("/start-session/")
async def start_session():
    session_id = str(uuid.uuid4())
    get_session_history(session_id)
    return {"session_id": session_id}

class FeedbackRequest(BaseModel):
    session_id: str






@app.post("/end-session/")
async def end_session_and_save_feedback(request: FeedbackRequest, token: dict = Depends(jwt_bearer)):
    decoded_token = decode_jwt(token)
    user_id = decoded_token.get("_id")
    session_id = request.session_id

    # Prepare feedback prompt
    feedback_prompt = (
        f"Дай строгий фидбэк по пройденному пользователем интервью. "
        f"Вот вся история интервью:\n\n\n"
        "Оцени его по следующим критериям:\n"
        "1. Софт Скиллы (коммуникация, командная работа, адаптивность и т.д.).\n"
        " - Оцениваешь строго, обрати внимание на конкретность и уместность высказываний.\n"
        "2. Хард Скиллы (укажите конкретные темы, которые он знает хорошо и те, которые требуют улучшения).\n"
        " - Строго проверяешь ответы на правильность и конкретность. Выявляй ошибки и недочеты.\n"
        "3. Рекомендации (предложите материалы или шаги для улучшения слабых навыков).\n"
        " - Дай конкретные рекомендации, как улучшить слабые стороны.\n"
        "Пример строгого фидбэка: 'Кандидат продемонстрировал недостаточную точность в объяснении алгоритмов. "
        "Некоторые ответы содержали избыточную информацию, не относящуюся к теме. Рекомендуем изучить книги XYZ и курсы ABC."
        "ДАЙ ФИДБЭК В ФОРМАТЕ БУЛЛЕТ ПОИНТОВ БЕЗ СИМВЛОВОВ ПРИМЕР: 1. 2. 3. 4. 5.'"
    )

    # Get chat history
    chat_history = get_session_history(session_id)
    
    # Combine messages and save in JSON format without duplicates
    combined_history = []
    last_message = None

    for msg in chat_history.messages[1:]:  # Skip the system prompt
        role = 'Human' if isinstance(msg, HumanMessage) else 'AI'
        content = msg.content.strip()
        
        if not last_message or (last_message["role"] != role or last_message["content"] != content):
            combined_history.append({"role": role, "content": content})
            last_message = {"role": role, "content": content}

    history_text = "\n".join([f"{message['role']}: {message['content']}" for message in combined_history])

    messages = [
        SystemMessage(content=feedback_prompt),
        HumanMessage(content=history_text)
    ]

    # Get AI feedback
    ai_feedback = model.invoke(messages)

    # Prepare session data including history
    session_data = {
        "_id": str(ObjectId()),
        "session_id": session_id,
        "user_id": user_id,
        "history": combined_history,
        "feedback": ai_feedback.content,
        "timestamp": time.time()
    }

    # Save session data to MongoDB
    await sessions_collection.insert_one(jsonable_encoder(session_data))
    
    return session_data


@app.get("/feedbacks/")
async def get_feedbacks(token: dict = Depends(jwt_bearer)):
    decoded_token = decode_jwt(token)
    user_id = decoded_token.get("_id")
    feedbacks = await sessions_collection.find({'user_id': user_id}).sort('timestamp', -1).to_list(length=100)
    return [
        {
            '_id': str(feedback.get("_id")),
            'feedback': feedback.get('feedback'),
            'history': feedback.get('history'),
            'timestamp': feedback.get('timestamp', '')
        } for feedback in feedbacks
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app='main:app', host="0.0.0.0", port=8002, reload=True, workers=4)

