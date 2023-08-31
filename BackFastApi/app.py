from fastapi import FastAPI
from controller.Task_Controller import router as TaskRouter


app = FastAPI()

app.include_router(TaskRouter)
