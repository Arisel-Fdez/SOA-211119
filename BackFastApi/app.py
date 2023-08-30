from fastapi import FastAPI
from controller.User_Controller import router as UserRouter
from controller.Alarma_Controller import router as AlarmaRouter
from controller.Chat_Controller import router as ChatRouter


app = FastAPI()

app.include_router(UserRouter)
app.include_router(AlarmaRouter)
app.include_router(ChatRouter)
