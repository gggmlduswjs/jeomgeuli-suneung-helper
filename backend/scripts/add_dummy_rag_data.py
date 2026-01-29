"""
RAG 추천 시스템에 더미 데이터 추가 스크립트
1강에 더미 개념/문제/본문 데이터를 추가하여 RAG 추천 기능 테스트

RAG 추천 시스템 원리:
1. 텍스트 → 벡터(임베딩) 변환: Sentence Transformers 모델 사용
2. 벡터 DB에 저장: FAISS 또는 Chroma 사용
3. 검색 쿼리도 벡터로 변환
4. 코사인 유사도로 가장 유사한 문서 찾기
5. 유사도 점수가 높은 순서로 추천
"""
import sys
import os
from pathlib import Path

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import Lesson
from app.infrastructure.ai.genai import GenAIProcessor

def add_dummy_rag_data(lesson_id: str = None):
    """
    1강에 더미 RAG 데이터 추가
    
    Args:
        lesson_id: 강의 ID (None이면 첫 번째 강의 사용)
    """
    db = next(get_db())
    
    try:
        # 1강 찾기
        if lesson_id:
            lesson = db.query(Lesson).filter(Lesson.lesson_id == lesson_id).first()
        else:
            # 첫 번째 강의 가져오기
            lesson = db.query(Lesson).first()
        
        if not lesson:
            print("❌ 강의를 찾을 수 없습니다.")
            return
        
        print(f"✅ 강의 찾음: {lesson.title} (ID: {lesson.lesson_id})")
        
        # GenAIProcessor 초기화
        print("\n📦 RAG 추천 시스템 초기화 중...")
        ai_processor = GenAIProcessor(
            enable_recommendations=True,
            vector_db_path=None  # 메모리 기반
        )
        recommender = ai_processor.rag_recommender
        
        if not recommender:
            print("❌ RAG 추천 시스템 초기화 실패")
            return
        
        print("✅ RAG 추천 시스템 초기화 완료\n")
        
        # 더미 개념 데이터
        dummy_concepts = [
            {
                'id': f'dummy_concept_1',
                'title': '시적 표현의 개념',
                'content': '시적 표현은 시에서 사용하는 특별한 언어 기법입니다. 비유, 상징, 은유 등을 통해 추상적인 감정이나 생각을 구체적으로 표현합니다.',
                'metadata': {
                    'type': 'concept',
                    'lesson_id': lesson.lesson_id,
                    'unit_id': 'dummy_concept_1',
                    'title': '시적 표현의 개념'
                }
            },
            {
                'id': f'dummy_concept_2',
                'title': '비유법',
                'content': '비유법은 한 대상을 다른 대상에 빗대어 표현하는 수사법입니다. 직유, 은유, 활유 등이 있습니다.',
                'metadata': {
                    'type': 'concept',
                    'lesson_id': lesson.lesson_id,
                    'unit_id': 'dummy_concept_2',
                    'title': '비유법'
                }
            },
            {
                'id': f'dummy_concept_3',
                'title': '상징',
                'content': '상징은 구체적인 사물이나 현상을 통해 추상적인 의미를 나타내는 표현 방법입니다.',
                'metadata': {
                    'type': 'concept',
                    'lesson_id': lesson.lesson_id,
                    'unit_id': 'dummy_concept_3',
                    'title': '상징'
                }
            },
        ]
        
        # 더미 문제 데이터
        dummy_problems = [
            {
                'id': f'dummy_problem_1',
                'question_text': '다음 중 시적 표현의 효과로 가장 적절한 것은? 1) 정보 전달 2) 감정 전달 3) 사실 설명 4) 논리 전개',
                'metadata': {
                    'type': 'problem',
                    'lesson_id': lesson.lesson_id,
                    'unit_id': 'dummy_problem_1',
                    'title': '시적 표현 효과 문제'
                }
            },
            {
                'id': f'dummy_problem_2',
                'question_text': '비유법의 종류로 옳지 않은 것은? 1) 직유 2) 은유 3) 활유 4) 대유',
                'metadata': {
                    'type': 'problem',
                    'lesson_id': lesson.lesson_id,
                    'unit_id': 'dummy_problem_2',
                    'title': '비유법 종류 문제'
                }
            },
        ]
        
        # 더미 본문 데이터
        dummy_passages = [
            {
                'id': f'dummy_passage_1',
                'content': '바람이 불어오는 방향을 따라가면, 그곳에는 새로운 세상이 기다리고 있다. 바람은 자유의 상징이며, 변화를 의미한다.',
                'metadata': {
                    'type': 'passage',
                    'lesson_id': lesson.lesson_id,
                    'unit_id': 'dummy_passage_1',
                    'title': '바람에 관한 시'
                }
            },
            {
                'id': f'dummy_passage_2',
                'content': '밤하늘의 별들은 고요히 빛나며, 우리에게 희망을 전해준다. 별은 어둠 속에서도 길을 비춰주는 등불과 같다.',
                'metadata': {
                    'type': 'passage',
                    'lesson_id': lesson.lesson_id,
                    'unit_id': 'dummy_passage_2',
                    'title': '별에 관한 시'
                }
            },
        ]
        
        # RAG 시스템에 추가
        print("📝 더미 데이터 추가 중...\n")
        
        # 개념 추가
        if dummy_concepts:
            recommender.add_concepts(dummy_concepts, text_field='content')
            print(f"✅ 개념 {len(dummy_concepts)}개 추가:")
            for concept in dummy_concepts:
                print(f"   - {concept['title']}")
        
        # 문제 추가
        if dummy_problems:
            recommender.add_problems(dummy_problems, text_field='question_text')
            print(f"\n✅ 문제 {len(dummy_problems)}개 추가:")
            for problem in dummy_problems:
                print(f"   - {problem['metadata']['title']}")
        
        # 본문 추가
        if dummy_passages:
            recommender.add_documents(
                [p['content'] for p in dummy_passages],
                [p['metadata'] for p in dummy_passages]
            )
            print(f"\n✅ 본문 {len(dummy_passages)}개 추가:")
            for passage in dummy_passages:
                print(f"   - {passage['metadata']['title']}")
        
        print(f"\n🎉 총 {len(dummy_concepts) + len(dummy_problems) + len(dummy_passages)}개의 더미 데이터 추가 완료!")
        print(f"\n📌 테스트 방법:")
        print(f"   1. 프론트엔드에서 '유사 콘텐츠 추천' 버튼 클릭")
        print(f"   2. 검색 쿼리 예시:")
        print(f"      - '시적 표현' → 시적 표현 관련 개념 추천")
        print(f"      - '비유법' → 비유법 관련 개념/문제 추천")
        print(f"      - '바람' → 바람 관련 본문 추천")
        print(f"      - '별' → 별 관련 본문 추천")
        
        # 테스트 검색
        print(f"\n🔍 테스트 검색 실행...\n")
        test_queries = ['시적 표현', '비유법', '바람']
        for query in test_queries:
            result = recommender.search(query, top_k=3)
            print(f"검색어: '{query}'")
            print(f"  → {len(result.recommendations)}개 결과:")
            for i, (rec, score) in enumerate(zip(result.recommendations, result.scores), 1):
                rec_text = rec.get('text', '') if isinstance(rec, dict) else str(rec)
                rec_meta = rec.get('metadata', {}) if isinstance(rec, dict) else {}
                title = rec_meta.get('title', '제목 없음')
                preview = rec_text[:50] + '...' if len(rec_text) > 50 else rec_text
                print(f"    {i}. [{title}] 유사도: {score:.3f}")
                print(f"       {preview}")
            print()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG 추천 시스템에 더미 데이터 추가')
    parser.add_argument('--lesson-id', type=str, help='강의 ID (선택사항, 없으면 첫 번째 강의 사용)')
    
    args = parser.parse_args()
    add_dummy_rag_data(args.lesson_id)
