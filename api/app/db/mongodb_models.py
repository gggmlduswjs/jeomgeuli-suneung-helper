"""
MongoDB 데이터 모델 정의
레슨 블록 기반 학습 시스템
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class BlockType(str, Enum):
    """레슨 블록 타입"""
    ORIENTATION = "orientation"
    LEARNING_GOAL = "learning_goal"
    EXAM_STRUCTURE = "exam_structure"
    APPRECIATION_FRAME = "appreciation_frame"
    WORK_ANALYSIS = "work_analysis"
    PROBLEM_APPLICATION = "problem_application"
    SUMMARY = "summary"
    CLOSING_MESSAGE = "closing_message"


class LearningIntent(BaseModel):
    """학습 목적"""
    title: str
    description: str


class AudioRange(BaseModel):
    """음성 강의 범위"""
    start: str  # "HH:MM:SS" 형식
    end: str


class UserAwareness(BaseModel):
    """사용자 인지 효과"""
    message: str
    context: str


class UIBehavior(BaseModel):
    """UI 동작 규칙"""
    autoPlay: bool = True
    bookmarkable: bool = True
    reviewable: bool = True
    pausePoints: Optional[List[str]] = None  # 자동 일시정지 지점
    navigationPoints: Optional[List[Dict[str, Any]]] = None  # 주요 전환 지점
    problemMode: Optional[bool] = None  # 문제 모드
    nextLesson: Optional[str] = None  # 다음 레슨 ID


class LessonBlock(BaseModel):
    """레슨 블록"""
    blockId: str
    type: BlockType
    order: int
    learningIntent: LearningIntent
    brailleSignal: str = Field(..., pattern=r'^[●○]{3}$')  # 3셀 점자 패턴
    audioRange: AudioRange
    userAwareness: UserAwareness
    uiBehavior: UIBehavior
    content: Dict[str, Any]  # 블록 타입별 가변 필드


class LessonProgress(BaseModel):
    """레슨 진행 상태"""
    userId: str
    currentBlock: Optional[str] = None  # 현재 블록 ID
    completedBlocks: List[str] = []  # 완료한 블록 ID 목록
    bookmarks: List[str] = []  # 북마크한 블록 ID 목록
    lastAccessed: Optional[datetime] = None


class LessonMetadata(BaseModel):
    """레슨 메타데이터"""
    year: int
    curriculum: str
    estimatedDuration: int  # 초 단위
    difficulty: Optional[str] = None


class Lesson(BaseModel):
    """레슨 문서"""
    lessonId: str
    subject: str  # "korean", "math", "english"
    title: str
    order: int
    metadata: LessonMetadata
    blocks: List[LessonBlock]  # 순서 중요
    progress: Optional[LessonProgress] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


# 블록 타입별 Content 스키마 예시
class OrientationContent(BaseModel):
    """오리엔테이션 블록 내용"""
    script: str
    keyPoints: List[str]


class LearningGoalContent(BaseModel):
    """학습 목표 블록 내용"""
    goals: List[str]
    prerequisites: Optional[List[str]] = None


class ExamStructureContent(BaseModel):
    """시험 구조 블록 내용"""
    structure: Dict[str, Any]
    examples: List[str]


class AppreciationFrameContent(BaseModel):
    """감상 프레임 블록 내용"""
    frame: str
    explanation: str
    examples: List[str]


class WorkAnalysisContent(BaseModel):
    """작품 분석 블록 내용"""
    work: Dict[str, Any]  # title, author, period, analysis 등


class ProblemApplicationContent(BaseModel):
    """문제 적용 블록 내용"""
    problemNumber: int
    question: str
    choices: List[str]
    correctAnswer: int
    explanation: str
    thinkingProcess: List[str]


class SummaryContent(BaseModel):
    """요약 블록 내용"""
    keyPoints: List[str]
    connections: List[str]


class ClosingMessageContent(BaseModel):
    """마무리 블록 내용"""
    message: str
    nextLessonPreview: Optional[str] = None
