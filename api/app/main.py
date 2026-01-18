"""
FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_db
from app.routers import health, books, lessons, units, progress, answers, review, syncpoints, pdf, lecture_scripts, curriculum, content, lesson_blocks

# 데이터베이스 초기화
init_db()

app = FastAPI(
    title="점글이 MVP 2.0 API",
    description="시각장애인을 위한 수능 학습 지원 API",
    version="2.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(books.router, prefix="/api/v1", tags=["books"])
app.include_router(lessons.router, prefix="/api/v1", tags=["lessons"])
app.include_router(units.router, prefix="/api/v1", tags=["units"])
app.include_router(progress.router, prefix="/api/v1", tags=["progress"])
app.include_router(answers.router, prefix="/api/v1", tags=["answers"])
app.include_router(review.router, prefix="/api/v1", tags=["review"])
app.include_router(syncpoints.router, prefix="/api/v1", tags=["syncpoints"])
app.include_router(pdf.router, prefix="/api/v1", tags=["pdf"])
app.include_router(lecture_scripts.router, tags=["lecture-scripts"])
app.include_router(curriculum.router, prefix="/api/v1", tags=["curriculum"])
app.include_router(content.router, prefix="/api/v1", tags=["content"])
app.include_router(lesson_blocks.router, prefix="/api/v1", tags=["lesson-blocks"])


@app.get("/")
async def root():
    return {"message": "점글이 MVP 2.0 API", "version": "2.0.0"}
