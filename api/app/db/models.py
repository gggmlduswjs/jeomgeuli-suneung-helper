"""
SQLAlchemy 데이터베이스 모델
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base


class ParseStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class Subject(str, enum.Enum):
    KOREAN = "KOREAN"
    ENGLISH = "ENGLISH"
    MATH = "MATH"


class UnitType(str, enum.Enum):
    CONCEPT_CORE = "CONCEPT_CORE"
    CONCEPT_FORM = "CONCEPT_FORM"
    CONCEPT_CONTENT = "CONCEPT_CONTENT"
    PASSAGE = "PASSAGE"
    QUESTION = "QUESTION"


class Book(Base):
    __tablename__ = "books"
    
    book_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    subject = Column(Enum(Subject), nullable=False)
    year = Column(Integer)
    parse_status = Column(Enum(ParseStatus), default=ParseStatus.PENDING)
    file_path = Column(String)  # PDF 저장 경로
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lessons = relationship("Lesson", back_populates="book", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lessons"
    
    lesson_id = Column(String, primary_key=True)
    book_id = Column(String, ForeignKey("books.book_id", ondelete="CASCADE"), nullable=False)
    index = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    lecture_script_text = Column(Text)  # 해당 레슨의 강의 대본 (레슨 단위로 분할된 것)
    estimated_time = Column(Integer)  # 예상 소요 시간 (분)
    key_points = Column(Text)  # JSON: ["핵심1", "핵심2"]
    has_question = Column(Boolean, default=False)  # 문제 풀이 포함 여부
    has_analysis = Column(Boolean, default=False)  # 작품 분석 포함 여부
    created_at = Column(DateTime, default=datetime.utcnow)
    
    book = relationship("Book", back_populates="lessons")
    units = relationship("Unit", back_populates="lesson", cascade="all, delete-orphan")
    syncpoints = relationship("Syncpoint", back_populates="lesson", cascade="all, delete-orphan")


class Unit(Base):
    __tablename__ = "units"
    
    unit_id = Column(String, primary_key=True)
    lesson_id = Column(String, ForeignKey("lessons.lesson_id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum(UnitType), nullable=False)
    title = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    content_text = Column(Text)  # 개념/지문 텍스트
    braille_text = Column(Text)  # 점자 변환 결과
    question_stem = Column(Text)  # 문제 지문
    question_choices = Column(Text)  # JSON: ["① ...", "② ..."]
    question_answer = Column(Integer)  # 정답 번호
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lesson = relationship("Lesson", back_populates="units")
    answers = relationship("Answer", back_populates="unit", cascade="all, delete-orphan")
    review_items = relationship("ReviewQueue", back_populates="unit", cascade="all, delete-orphan")


class Syncpoint(Base):
    __tablename__ = "syncpoints"
    
    syncpoint_id = Column(String, primary_key=True)
    lesson_id = Column(String, ForeignKey("lessons.lesson_id", ondelete="CASCADE"), nullable=False)
    timestamp_sec = Column(Float, nullable=False)
    hint_type = Column(String)  # "개념", "예시", "문제", "정리"
    unit_id = Column(String, ForeignKey("units.unit_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    lesson = relationship("Lesson", back_populates="syncpoints")
    unit = relationship("Unit")
    logs = relationship("SyncLog", back_populates="syncpoint", cascade="all, delete-orphan")


class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    book_id = Column(String, ForeignKey("books.book_id", ondelete="SET NULL"), nullable=True)
    lesson_id = Column(String, ForeignKey("lessons.lesson_id", ondelete="SET NULL"), nullable=True)
    unit_id = Column(String, ForeignKey("units.unit_id", ondelete="SET NULL"), nullable=True)
    syncpoint_id = Column(String, ForeignKey("syncpoints.syncpoint_id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Answer(Base):
    __tablename__ = "answers"
    
    answer_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    unit_id = Column(String, ForeignKey("units.unit_id", ondelete="CASCADE"), nullable=False)
    selected = Column(Integer)  # 선택한 답안 번호
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    unit = relationship("Unit", back_populates="answers")


class ReviewQueue(Base):
    __tablename__ = "review_queue"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    unit_id = Column(String, ForeignKey("units.unit_id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(String, ForeignKey("lessons.lesson_id", ondelete="SET NULL"), nullable=True)
    reason = Column(String)  # "WRONG", "WRONG_REPEATED"
    priority = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    unit = relationship("Unit", back_populates="review_items")


class SyncLog(Base):
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    lesson_id = Column(String, ForeignKey("lessons.lesson_id", ondelete="SET NULL"), nullable=True)
    syncpoint_id = Column(String, ForeignKey("syncpoints.syncpoint_id", ondelete="SET NULL"), nullable=True)
    event = Column(String)  # "BEEP_PLAYED", "JUMP_CLICKED", "SCROLLED", "IGNORED"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    syncpoint = relationship("Syncpoint", back_populates="logs")


class CurriculumStatus(str, enum.Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    DONE = "DONE"
    FAILED = "FAILED"


class Curriculum(Base):
    __tablename__ = "curricula"
    
    curriculum_id = Column(String, primary_key=True)
    book_id = Column(String, ForeignKey("books.book_id", ondelete="SET NULL"), nullable=True)
    subject = Column(Enum(Subject), nullable=False)
    title = Column(String, nullable=False)
    status = Column(Enum(CurriculumStatus), default=CurriculumStatus.PENDING)
    lesson_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    learning_units = relationship("LearningUnit", back_populates="curriculum", cascade="all, delete-orphan")
    book = relationship("Book")


class LearningUnit(Base):
    __tablename__ = "learning_units"
    
    unit_id = Column(String, primary_key=True)
    curriculum_id = Column(String, ForeignKey("curricula.curriculum_id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(String, ForeignKey("lessons.lesson_id", ondelete="SET NULL"), nullable=True)
    section_type = Column(String, nullable=False)  # 과목별 타입: "concept", "example", "strategy", "problem" 등
    title = Column(String)  # 학습 단위 제목 (예: "Unit 1. 수학Ⅰ 전체 맵 이해")
    content = Column(Text, nullable=False)  # 전체 내용 텍스트
    order = Column(Integer, nullable=False)
    
    # 공통 구조 필드 (과목 공통)
    learning_objective = Column(Text)  # 학습 목표
    key_content = Column(Text)  # 핵심 내용
    learning_point = Column(Text)  # 학습 포인트
    
    # 점자/음성 지원 필드
    braille_pattern = Column(Text)  # JSON: [1,2,3] - 점자 3셀 패턴 (상태 전환 신호용)
    braille_text = Column(Text)  # 점자 변환 결과 (전체)
    tts_text = Column(Text)  # TTS용 요약 텍스트
    
    # 분할 및 참조 정보
    break_points = Column(Text)  # JSON: ["자, 그다음에...", "먼저..."] - 말하는 단위 분할 지점
    pdf_references = Column(Text)  # JSON: [{"type": "problem", "number": 1}, ...]
    
    # 과목별 확장 정보 (JSON)
    subject_metadata = Column(Text)  # JSON: 과목별 특화 정보 (예: {"work_title": "...", "expression_type": "..."})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    curriculum = relationship("Curriculum", back_populates="learning_units")
    lesson = relationship("Lesson")


class CurriculumTemplate(Base):
    __tablename__ = "curriculum_templates"
    
    template_id = Column(String, primary_key=True)
    subject = Column(Enum(Subject), nullable=False, unique=True)
    structure = Column(Text, nullable=False)  # JSON: 교재 구조 정의
    dependency_rules = Column(Text)  # JSON: 의존성 규칙 정의
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)