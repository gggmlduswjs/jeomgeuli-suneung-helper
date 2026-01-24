"""
EBS 수능특강 문학 교재 전체 분석 스크립트
1강~80강 전체를 분석하여 개념/본문/문제 유닛으로 구조화하고 JSON 출력
"""
import sys
import json
from pathlib import Path

# backend 경로 추가
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.infrastructure.pdf.pipeline import UnifiedPipeline
from app.core.config import settings


def extract_and_format_literature(pdf_path: str, output_path: str):
    """
    문학 PDF를 분석하여 사용자 요청 형식의 JSON으로 변환

    Args:
        pdf_path: PDF 파일 경로
        output_path: 출력 JSON 파일 경로
    """
    print(f"\n{'='*60}")
    print(f"EBS 수능특강 문학 교재 전체 분석")
    print(f"{'='*60}\n")

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

    print(f"[PDF] {pdf_path}")
    print(f"[OUTPUT] {output_path}\n")

    # 1. UnifiedPipeline으로 전체 추출
    print("[1단계] PDF 텍스트 추출 및 파싱 중...")
    pipeline = UnifiedPipeline(
        subject='literature',
        use_ocr='auto',  # 자동 모드: 텍스트 레이어 확인 후 필요시 OCR 전환
        save_results=False,  # 기본 결과 저장 비활성화
        book_id=None
    )

    result = pipeline.process(pdf_path)

    lectures = result.get('lectures', [])
    lecture_contents = result.get('lecture_contents', [])
    problems = result.get('problems', [])

    print(f"[OK] 추출 완료: {len(lectures)}개 강의, {len(problems)}개 문제\n")

    # 2. 사용자 요청 형식으로 변환
    print("[2단계] 데이터 구조 변환 중...")
    formatted_lectures = []

    for lecture in lectures:
        lecture_id = lecture['lecture_id']
        lecture_title = lecture['title']

        # 해당 강의의 콘텐츠 찾기
        lecture_content = next(
            (lc for lc in lecture_contents if lc['lecture_id'] == lecture_id),
            None
        )

        if not lecture_content:
            print(f"[WARN] 강의 {lecture_id}의 콘텐츠를 찾을 수 없습니다.")
            formatted_lectures.append({
                "lecture_id": lecture_id,
                "lecture_title": lecture_title,
                "start_page": lecture.get('page', 0),
                "end_page": lecture.get('page', 0),
                "units": {
                    "concept": [],
                    "passage": [],
                    "question": []
                }
            })
            continue

        start_page = lecture_content.get('start_page', lecture.get('page', 0))
        end_page = lecture_content.get('end_page', lecture.get('page', 0))
        sections = lecture_content.get('sections', [])

        # 유닛 구조 생성
        concept_units = []
        passage_units = []

        for section in sections:
            section_type = section.get('type', 'concept')
            section_title = section.get('title', '')
            section_content = section.get('content', [])

            # content가 리스트면 합치기
            if isinstance(section_content, list):
                content_text = '\n'.join(section_content)
            else:
                content_text = str(section_content)

            if section_type == 'concept':
                concept_units.append({
                    "title": section_title,
                    "content": content_text
                })
            elif section_type in ['content', 'passage']:
                # 본문 섹션: 제목에서 작품명과 저자 추출 시도
                # 예: "작품으로 이해하기 - 박두진, 「해」"
                work_title = ""
                author = ""

                # 제목에서 작품 정보 추출
                if '-' in section_title:
                    parts = section_title.split('-', 1)
                    if len(parts) > 1:
                        work_info = parts[1].strip()
                        # "박두진, 「해」" 형식 파싱
                        if ',' in work_info:
                            author, work_title = work_info.split(',', 1)
                            author = author.strip()
                            work_title = work_title.strip()
                        elif '「' in work_info or '[' in work_info:
                            work_title = work_info
                        else:
                            author = work_info

                passage_units.append({
                    "work_title": work_title,
                    "author": author,
                    "text": content_text
                })

        # 문제 유닛: 해당 강의 페이지 범위 내의 문제들
        question_units = []
        for problem in problems:
            problem_page = problem.get('page', 0)
            if start_page <= problem_page <= end_page:
                # 문제 상세 정보가 있으면 사용, 없으면 기본 구조
                question_units.append({
                    "question_type": "객관식",  # 기본값
                    "question_text": f"문제 {problem.get('problem_id', '')}",
                    "choices": []
                })

        formatted_lectures.append({
            "lecture_id": lecture_id,
            "lecture_title": lecture_title,
            "start_page": start_page,
            "end_page": end_page,
            "units": {
                "concept": concept_units,
                "passage": passage_units,
                "question": question_units
            }
        })

    # lecture_id 순서대로 정렬
    formatted_lectures.sort(key=lambda x: x['lecture_id'])

    print(f"[OK] 변환 완료: {len(formatted_lectures)}개 강의\n")

    # 3. JSON 파일로 저장
    print(f"[3단계] JSON 파일 저장 중...")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_lectures, f, ensure_ascii=False, indent=2)

    print(f"[OK] 저장 완료: {output_path}\n")

    # 4. 요약 정보 출력
    print(f"{'='*60}")
    print(f"분석 완료 요약")
    print(f"{'='*60}")
    print(f"총 강의 수: {len(formatted_lectures)}")

    total_concepts = sum(len(lec['units']['concept']) for lec in formatted_lectures)
    total_passages = sum(len(lec['units']['passage']) for lec in formatted_lectures)
    total_questions = sum(len(lec['units']['question']) for lec in formatted_lectures)

    print(f"총 개념 유닛: {total_concepts}")
    print(f"총 본문 유닛: {total_passages}")
    print(f"총 문제 유닛: {total_questions}")
    print(f"{'='*60}\n")

    # 강의별 상세 정보
    print("강의별 상세:")
    for lec in formatted_lectures[:10]:  # 처음 10개만 출력
        print(f"  {lec['lecture_id']:2d}강: {lec['lecture_title'][:40]:40s} "
              f"(페이지 {lec['start_page']:3d}-{lec['end_page']:3d}) "
              f"- 개념:{len(lec['units']['concept']):2d} 본문:{len(lec['units']['passage']):2d} 문제:{len(lec['units']['question']):2d}")

    if len(formatted_lectures) > 10:
        print(f"  ... (나머지 {len(formatted_lectures) - 10}개 강의)")

    print()


if __name__ == "__main__":
    # PDF 경로와 출력 경로 설정
    pdf_path = r"data\pdfs\2026 수능특강_ 문학.pdf"
    output_path = r"literature_full_analysis.json"

    try:
        extract_and_format_literature(pdf_path, output_path)
        print("[OK] 모든 작업 완료!")
    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
