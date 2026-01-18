"""
복습 로직 서비스
오답 우선순위 규칙 및 복습 큐 생성
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.db.models import Answer, ReviewQueue, Unit


def create_review_queue_for_wrong_answers(
    user_id: str,
    unit_id: str,
    db: Session,
) -> None:
    """
    오답에 대한 복습 큐 항목 생성
    
    Args:
        user_id: 사용자 ID
        unit_id: 학습 단위 ID
        db: 데이터베이스 세션
    """
    # 해당 Unit의 오답 기록 확인
    wrong_answers = db.query(Answer).filter(
        Answer.user_id == user_id,
        Answer.unit_id == unit_id,
        Answer.is_correct == False,
    ).all()
    
    if not wrong_answers:
        return
    
    # 반복 오답 여부 확인
    wrong_count = len(wrong_answers)
    is_repeated = wrong_count > 1
    
    # 기존 복습 큐 항목 확인
    existing = db.query(ReviewQueue).filter(
        ReviewQueue.user_id == user_id,
        ReviewQueue.unit_id == unit_id,
        ReviewQueue.completed == False,
    ).first()
    
    if existing:
        # 우선순위 업데이트
        existing.reason = "WRONG_REPEATED" if is_repeated else "WRONG"
        existing.priority = 0 if is_repeated else 1
    else:
        # 새 항목 생성
        unit = db.query(Unit).filter(Unit.unit_id == unit_id).first()
        review_item = ReviewQueue(
            user_id=user_id,
            unit_id=unit_id,
            lesson_id=unit.lesson_id if unit else None,
            reason="WRONG_REPEATED" if is_repeated else "WRONG",
            priority=0 if is_repeated else 1,
            completed=False,
        )
        db.add(review_item)
    
    db.commit()


def get_review_queue_with_priority(
    user_id: str,
    book_id: str = None,
    db: Session = None,
) -> List[ReviewQueue]:
    """
    우선순위가 적용된 복습 큐 조회
    
    Args:
        user_id: 사용자 ID
        book_id: 교재 ID (선택)
        db: 데이터베이스 세션
    
    Returns:
        복습 큐 항목 리스트 (우선순위 순)
    """
    query = db.query(ReviewQueue).filter(
        ReviewQueue.user_id == user_id,
        ReviewQueue.completed == False,
    )
    
    # book_id 필터링 (선택)
    if book_id:
        from app.db.models import Lesson
        query = query.join(Unit).join(Lesson).filter(Lesson.book_id == book_id)
    
    # 우선순위 순으로 정렬
    items = query.order_by(
        ReviewQueue.priority.desc(),
        ReviewQueue.created_at.desc()
    ).all()
    
    return items
