"""
전체 파싱 모드 관련 파일들

이 폴더에는 전체 파싱 모드(UnifiedPipeline)에서 사용하는 파일들이 있습니다.
간단 모드에서는 이 파일들을 사용하지 않습니다.

주요 파일:
- pipeline.py: UnifiedPipeline 클래스
- parsers/: 과목별 파서 (literature, math1, english 등)
- postprocessors/: 후처리 (중복 제거, 분류 등)
- lecture_contents_extractor.py: 강의 콘텐츠 추출
- result_saver.py: 결과 저장
- image_saver.py: 이미지 저장
- extractor_factory.py: 추출기 팩토리
- page_range_calculator.py: 페이지 범위 계산
"""
