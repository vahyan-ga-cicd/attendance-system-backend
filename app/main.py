# import os
# os.environ['FLAGS_use_mkldnn'] = '0'
# os.environ['PADDLE_ONEDNN_OPTERS'] = '0'
# os.environ['PADDLE_WITH_MKLDNN'] = 'OFF'

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from app.api.v1.routes import documents
from mangum import Mangum


from app.api.v1.routes import employee, attendance

app = FastAPI(
    title="Employee Attendance System",
    description="Face recognition and eye blink based attendance management",
    version="1.0.0"
)

app.include_router(employee.router, prefix="/api/v1/employee", tags=["Employee"])
app.include_router(attendance.router, prefix="/api/v1/attendance", tags=["Attendance"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




handler = Mangum(app)


@app.get("/")
async def root():
    return {"message": "Welcome to the Attendence Management System. Go to /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
