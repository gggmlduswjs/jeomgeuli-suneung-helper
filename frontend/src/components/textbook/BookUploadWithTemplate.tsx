/**
 * 교재 업로드 + 템플릿 생성 통합 플로우
 * 설문조사 → YOLO 영역 마킹 → TOC 입력 → 템플릿 생성 → 파싱
 */
import { useState, useEffect } from 'react';
import { booksAPI } from '../../services/api/client';
import { templatesAPI, type ParsingGuideRegion, type CurriculumStructureSurvey, type ParsingTemplate } from '../../services/templates';
import type { Book } from '../../types/book';
import { Subject } from '../../types/book';
import PDFBboxMarker from '../admin/PDFBboxMarker';
import FileUploadStep from './steps/FileUploadStep';
import TemplateSelectStep from './steps/TemplateSelectStep';
import SurveyStep from './steps/SurveyStep';
import TOCInputStep from './steps/TOCInputStep';
import { ChevronLeft, ChevronRight, Image as ImageIcon, Sparkles, Check, Upload } from 'lucide-react';

interface BookUploadWithTemplateProps {
  onUploadComplete: (book: Book) => void;
  onSpeak?: (text: string) => void;
  onCancel?: () => void;
}

type Step = 'file' | 'template' | 'survey' | 'bbox' | 'toc' | 'generating' | 'parsing';

const SUBJECT_MAP: Record<Subject, 'literature' | 'math1' | 'english'> = {
  [Subject.KOREAN]: 'literature',
  [Subject.ENGLISH]: 'english',
  [Subject.MATH]: 'math1',
};

export default function BookUploadWithTemplate({ onUploadComplete, onSpeak, onCancel }: BookUploadWithTemplateProps) {
  const [step, setStep] = useState<Step>('file');
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState<Subject>(Subject.KOREAN);
  const [year, setYear] = useState<number>(new Date().getFullYear());
  
  // 설문조사
  const [curriculumSurvey, setCurriculumSurvey] = useState<CurriculumStructureSurvey>({
    is_lecture_based: true,
    lecture_units: ['concept', 'passage', 'problem'],
    unit_order: ['concept', 'passage', 'problem'],
  });
  
  // bbox 마킹
  const [parsingGuideRegions, setParsingGuideRegions] = useState<ParsingGuideRegion[]>([]);
  const [showBboxMarker, setShowBboxMarker] = useState(false);
  const [selectedPageForMarking, setSelectedPageForMarking] = useState<string>('1');
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);
  
  // TOC 입력
  const [tocPages, setTocPages] = useState('3,4,5');
  const [tocText, setTocText] = useState('');
  const [tocLectureExamples, setTocLectureExamples] = useState('');
  const [tocNonLectureExamples, setTocNonLectureExamples] = useState('');
  const [expectedLectureCount, setExpectedLectureCount] = useState('');

  // 텍스트 자동 추출
  const [extractingTocText, setExtractingTocText] = useState(false);
  const [cleaningTocText, setCleaningTocText] = useState(false);
  const [customCleaningPrompt, setCustomCleaningPrompt] = useState('');
  const [extractingText, setExtractingText] = useState(false);
  const [extractedTextExamples, setExtractedTextExamples] = useState<{ [key: string]: string[] } | null>(null);
  const [samplePagesForExtraction, setSamplePagesForExtraction] = useState<string>('15,30,50');

  // 템플릿 선택
  const [availableTemplates, setAvailableTemplates] = useState<ParsingTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<ParsingTemplate | null>(null);
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  // 상태
  const [generating, setGenerating] = useState(false);
  const [_parsing, setParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedTemplate, setGeneratedTemplate] = useState<{ name: string; warnings?: string[] } | null>(null);

  // 과목 변경 시 템플릿 로드
  useEffect(() => {
    if (step === 'template' && subject) {
      loadTemplates();
    }
  }, [step, subject]);

  const loadTemplates = async () => {
    setLoadingTemplates(true);
    try {
      const templates = await templatesAPI.list(SUBJECT_MAP[subject]);
      setAvailableTemplates(templates);
    } catch (err) {
      console.error('Failed to load templates:', err);
      setAvailableTemplates([]);
    } finally {
      setLoadingTemplates(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type !== 'application/pdf') {
        setError('PDF 파일만 업로드 가능합니다.');
        onSpeak?.('PDF 파일만 업로드 가능합니다.');
        return;
      }
      setFile(selectedFile);
      setError(null);
      
      // 파일명에서 제목 추출
      const fileName = selectedFile.name.replace(/\.pdf$/i, '');
      if (!title) {
        setTitle(fileName);
      }
      
      // PDF 미리보기 URL 생성
      const url = URL.createObjectURL(selectedFile);
      setPdfPreviewUrl(url);
    }
  };

  const handleNext = () => {
    if (step === 'file') {
      if (!file) {
        setError('PDF 파일을 선택해주세요.');
        onSpeak?.('PDF 파일을 선택해주세요.');
        return;
      }
      setStep('template');
    } else if (step === 'template') {
      if (selectedTemplate) {
        // 템플릿 선택 시 바로 파싱
        handleParseWithTemplate();
      } else {
        // 템플릿 미선택 시 템플릿 생성 흐름
        setStep('survey');
      }
    } else if (step === 'survey') {
      setStep('bbox');
    } else if (step === 'bbox') {
      setStep('toc');
    } else if (step === 'toc') {
      handleGenerateTemplate();
    }
  };

  const handleBack = () => {
    if (step === 'template') {
      setStep('file');
    } else if (step === 'survey') {
      setStep('template');
    } else if (step === 'bbox') {
      setStep('survey');
    } else if (step === 'toc') {
      setStep('bbox');
    }
  };

  const handleParseWithTemplate = async () => {
    if (!file || !selectedTemplate) {
      setError('파일과 템플릿을 선택해주세요.');
      return;
    }

    setStep('parsing');
    setParsing(true);
    setError(null);

    try {
      const book = await booksAPI.upload(file, title, subject, year, {
        enable_ml_deduplication: true,
        enable_ml_classification: true,
        enable_layout_analysis: false,
        enable_math_recognition: false,
        enable_llm_metadata: false,
        enable_llm_explanations: false,
        enable_llm_recommendations: false,
        openai_api_key: '',
        education_level: 'high',
      });

      onSpeak?.(`${book.title} 업로드 및 파싱이 시작되었습니다.`);
      onUploadComplete(book);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '업로드 중 오류가 발생했습니다.';
      setError(errorMsg);
      onSpeak?.(errorMsg);
      setParsing(false);
      setStep('template');
    }
  };

  const handleSkipBbox = () => {
    setStep('toc');
  };

  // bbox 마킹 페이지가 변경되면 샘플 페이지 자동 업데이트
  useEffect(() => {
    if (parsingGuideRegions.length > 0) {
      // 마킹된 페이지 번호 추출 (중복 제거)
      const markedPages = [...new Set(parsingGuideRegions.map(r => r.page))];
      markedPages.sort((a, b) => a - b);
      setSamplePagesForExtraction(markedPages.join(','));
    }
  }, [parsingGuideRegions]);

  const handleExtractTocText = async () => {
    if (!file) {
      onSpeak?.('PDF 파일이 필요합니다.');
      return;
    }

    if (!tocPages.trim()) {
      onSpeak?.('목차 페이지 번호를 입력해주세요 (예: 3,4,5).');
      return;
    }

    setExtractingTocText(true);
    setError(null);
    try {
      const result = await templatesAPI.extractTocText(file, tocPages);
      setTocText(result.toc_text);

      const pageCount = result.pages_extracted.length;
      const lineCount = result.total_lines;

      if (lineCount === 0) {
        onSpeak?.('목차 텍스트를 추출하지 못했습니다. 페이지 번호를 확인해주세요.');
        setError('목차 텍스트 추출 실패: 페이지 번호가 잘못되었거나 텍스트가 없을 수 있습니다.');
      } else {
        onSpeak?.(`${pageCount}개 페이지에서 ${lineCount}줄의 목차 텍스트를 추출했습니다. 검토 후 수정하세요.`);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '목차 텍스트 추출 중 오류가 발생했습니다.';
      onSpeak?.(message);
      setError(message);
      console.error('목차 텍스트 추출 오류:', err);
    } finally {
      setExtractingTocText(false);
    }
  };

  const handleCleanTocText = async () => {
    if (!tocText || tocText.trim().length < 20) {
      onSpeak?.('목차 텍스트를 먼저 입력해주세요.');
      return;
    }

    setCleaningTocText(true);
    setError(null);
    try {
      const result = await templatesAPI.cleanTocText(
        tocText,
        customCleaningPrompt.trim() || undefined
      );
      setTocText(result.cleaned_text);

      const ruleType = customCleaningPrompt.trim() ? '커스텀 규칙' : '기본 규칙';
      onSpeak?.(`목차 텍스트를 정제했습니다 (${ruleType}). ${result.changes_made}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '목차 텍스트 정제 중 오류가 발생했습니다.';
      onSpeak?.(message);
      setError(message);
      console.error('목차 텍스트 정제 오류:', err);
    } finally {
      setCleaningTocText(false);
    }
  };

  const handleExtractTextExamples = async () => {
    if (!file) {
      onSpeak?.('PDF 파일이 필요합니다.');
      return;
    }

    // region_hints 기본값 (과목별)
    type RegionConfig = { [regionName: string]: { y_min: number; y_max: number } };
    const defaultRegionHints: { [subject: string]: RegionConfig } = {
      [Subject.KOREAN]: {
        'concept': { y_min: 0.11, y_max: 0.84 },
        'passage': { y_min: 0.12, y_max: 0.54 },
        'problem': { y_min: 0.10, y_max: 0.81 }
      },
      [Subject.MATH]: {
        'concept': { y_min: 0.10, y_max: 0.80 },
        'passage': { y_min: 0.15, y_max: 0.50 },
        'problem': { y_min: 0.12, y_max: 0.85 }
      },
      [Subject.ENGLISH]: {
        'concept': { y_min: 0.10, y_max: 0.75 },
        'passage': { y_min: 0.15, y_max: 0.55 },
        'problem': { y_min: 0.12, y_max: 0.80 }
      }
    };

    const regionHints = defaultRegionHints[subject] || defaultRegionHints[Subject.KOREAN];

    // 샘플 페이지 파싱
    const pages = samplePagesForExtraction
      .split(',')
      .map(p => parseInt(p.trim()))
      .filter(p => !isNaN(p) && p > 0);

    if (pages.length === 0) {
      onSpeak?.('샘플 페이지를 입력해주세요 (예: 9,15,20)');
      return;
    }

    setExtractingText(true);
    try {
      const result = await templatesAPI.extractTextExamples(
        file,
        SUBJECT_MAP[subject],
        regionHints,
        pages,
        parsingGuideRegions.length > 0 ? parsingGuideRegions : undefined
      );

      setExtractedTextExamples(result.region_text_examples);

      // 결과에 따른 피드백
      const totalExamples = result.total_examples;
      if (totalExamples === 0) {
        onSpeak?.('텍스트를 추출하지 못했습니다. 다른 페이지를 시도해보세요.');
        setError('텍스트 추출 실패: 샘플 페이지에 개념/본문/문제가 없거나 텍스트가 이미지일 수 있습니다. 다른 페이지 번호를 시도하세요.');
      } else if (totalExamples < 10) {
        onSpeak?.(`${result.pages_processed}개 페이지에서 ${totalExamples}개 텍스트 예시를 추출했습니다. 더 많은 예시를 원하면 다른 페이지를 추가하세요.`);
        if ((result as any).debug?.warning) {
          setError((result as any).debug.warning + ' ' + ((result as any).debug.suggestion || ''));
        }
      } else {
        onSpeak?.(`${result.pages_processed}개 페이지에서 ${totalExamples}개 텍스트 예시를 추출했습니다.`);
        setError(null); // 성공 시 이전 에러 제거
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '텍스트 추출 중 오류가 발생했습니다.';
      setError(errorMsg);
      onSpeak?.(errorMsg);
    } finally {
      setExtractingText(false);
    }
  };

  const handleStartParsing = async () => {
    if (!file) {
      setError('PDF 파일이 없습니다.');
      return;
    }

    setStep('parsing');
    setParsing(true);
    setError(null);

    try {
      const book = await booksAPI.upload(file, title, subject, year, {
        enable_ml_deduplication: true,
        enable_ml_classification: true,
        enable_layout_analysis: false,
        enable_math_recognition: false,
        enable_llm_metadata: false,
        enable_llm_explanations: false,
        enable_llm_recommendations: false,
        openai_api_key: '',
        education_level: 'high',
      });

      onSpeak?.(`${book.title} 업로드 및 파싱이 시작되었습니다.`);
      onUploadComplete(book);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '파싱 시작 중 오류가 발생했습니다.';
      setError(errorMsg);
      onSpeak?.(errorMsg);
      setParsing(false);
      setStep('toc');
    }
  };

  const handleGenerateTemplate = async () => {
    if (!file || !tocText.trim() || tocText.trim().length < 20) {
      setError('TOC 텍스트를 입력해주세요.');
      onSpeak?.('TOC 텍스트를 입력해주세요.');
      return;
    }

    const lectureExamples = tocLectureExamples
      .split('\n')
      .map(s => s.trim())
      .filter(Boolean);
    
    if (lectureExamples.length < 1) {
      setError('TOC 강의 라인 예시를 최소 1줄 이상 입력해주세요.');
      onSpeak?.('TOC 강의 라인 예시를 최소 1줄 이상 입력해주세요.');
      return;
    }

    setStep('generating');
    setGenerating(true);
    setError(null);

    try {
      const templateName = `ebs_수능특강_${SUBJECT_MAP[subject]}_${year}`;

      // 추출된 텍스트 예시가 있으면 defaults에 포함
      const defaultsWithTextExamples: Record<string, unknown> = {
        toc_end_page: 7,
        start_content_page: 8,
        paragraph_y_threshold: 25,
      };

      if (extractedTextExamples && Object.keys(extractedTextExamples).length > 0) {
        defaultsWithTextExamples.region_text_examples = extractedTextExamples;
      }

      // 템플릿 생성
      const res = await templatesAPI.generateFromToc({
        subject: SUBJECT_MAP[subject],
        name: templateName,
        version: String(year),
        description: `${title} 템플릿`,
        year: year,
        book_name: title,
        toc_text: tocText,
        curriculum_survey: curriculumSurvey,
        parsing_guide_regions: parsingGuideRegions.length > 0 ? parsingGuideRegions : [],
        toc_lecture_line_examples: lectureExamples,
        toc_nonlecture_line_examples: tocNonLectureExamples
          .split('\n')
          .map(s => s.trim())
          .filter(Boolean),
        expected_lecture_count: expectedLectureCount ? parseInt(expectedLectureCount, 10) : undefined,
        save: true, // 즉시 저장
        model_name: 'gpt-4o-mini',
        confidence: 0.85,
        defaults: defaultsWithTextExamples,
      });

      // 생성된 템플릿 정보 저장
      setGeneratedTemplate({
        name: templateName,
        warnings: res.template?._notes || []
      });

      onSpeak?.('템플릿이 생성되었습니다. 파싱을 시작할 수 있습니다.');
      setGenerating(false);
      // generating 단계 유지 (템플릿 생성 완료 화면 표시)
    } catch (err: unknown) {
      // 에러 메시지 추출 (FastAPI의 detail 필드 우선)
      let errorMsg = '템플릿 생성 또는 업로드 중 오류가 발생했습니다.';

      // API 에러 응답에서 detail 추출
      if (err && typeof err === 'object' && 'response' in err) {
        const response = (err as { response?: { data?: { detail?: unknown } } }).response;
        const detail = response?.data?.detail;
        if (detail) {
          if (typeof detail === 'object' && detail !== null) {
            // 객체인 경우 message 필드 추출
            const detailObj = detail as { message?: string; detail?: string };
            errorMsg = detailObj.message || detailObj.detail || JSON.stringify(detail);
          } else {
            errorMsg = String(detail);
          }
        } else if (err instanceof Error) {
          errorMsg = err.message;
        }
      } else if (err instanceof Error) {
        errorMsg = err.message;
      } else if (typeof err === 'string') {
        errorMsg = err;
      }
      
      console.error('템플릿 생성 에러:', err);
      setError(errorMsg);
      onSpeak?.(errorMsg);
      setGenerating(false);
      setStep('toc');
    }
  };

  // Step 1: 파일 선택
  if (step === 'file') {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">1단계: PDF 파일 선택</h2>

        <FileUploadStep
          file={file}
          title={title}
          subject={subject}
          year={year}
          onFileChange={handleFileChange}
          onTitleChange={setTitle}
          onSubjectChange={setSubject}
          onYearChange={setYear}
          error={error}
        />

        <div className="flex gap-2 mt-4">
          {onCancel && (
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80"
            >
              취소
            </button>
          )}
          <button
            onClick={handleNext}
            disabled={!file}
            className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            다음
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  // Step 2: 템플릿 선택
  if (step === 'template') {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <button
            onClick={handleBack}
            className="p-1 hover:bg-secondary rounded"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <h2 className="text-xl font-bold">2단계: 템플릿 선택 (선택)</h2>
        </div>

        <TemplateSelectStep
          availableTemplates={availableTemplates}
          selectedTemplate={selectedTemplate}
          loadingTemplates={loadingTemplates}
          onTemplateSelect={setSelectedTemplate}
          onCreateNew={() => setSelectedTemplate(null)}
        />

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-3 mt-4">
            <p className="text-error text-sm">{error}</p>
          </div>
        )}

        <div className="flex gap-2 mt-4">
          <button
            onClick={handleBack}
            className="flex-1 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 flex items-center justify-center gap-2"
          >
            <ChevronLeft className="w-4 h-4" />
            이전
          </button>
          <button
            onClick={handleNext}
            className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 flex items-center justify-center gap-2"
          >
            {selectedTemplate ? (
              <>
                <Upload className="w-4 h-4" />
                템플릿 사용하여 파싱 시작
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                새 템플릿 생성하기
              </>
            )}
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  // Step 3: 설문조사
  if (step === 'survey') {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <button
            onClick={handleBack}
            className="p-1 hover:bg-secondary rounded"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <h2 className="text-xl font-bold">3단계: 커리큘럼 구조 설문</h2>
        </div>

        <SurveyStep
          survey={curriculumSurvey}
          onSurveyChange={setCurriculumSurvey}
        />

        <div className="flex gap-2 mt-4">
          <button
            onClick={handleBack}
            className="flex-1 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 flex items-center justify-center gap-2"
          >
            <ChevronLeft className="w-4 h-4" />
            이전
          </button>
          <button
            onClick={handleNext}
            className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 flex items-center justify-center gap-2"
          >
            다음
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  // Step 4: bbox 마킹
  if (step === 'bbox') {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <button
            onClick={handleBack}
            className="p-1 hover:bg-secondary rounded"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <h2 className="text-xl font-bold">4단계: 파싱 가이드 영역 마킹 (선택, 권장)</h2>
        </div>

        <div className="space-y-4">
          <div className="bg-muted/30 rounded-lg p-4">
            <p className="text-sm text-muted-foreground mb-4">
              3-5개 대표 페이지에서 개념/본문/문제 영역을 마킹하면 파싱 정확도가 크게 향상됩니다.
            </p>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <label className="block text-sm font-medium">페이지 번호</label>
                <input
                  type="number"
                  value={selectedPageForMarking}
                  onChange={(e) => {
                    const value = e.target.value;
                    // 빈 값도 허용 (입력 중)
                    setSelectedPageForMarking(value);
                  }}
                  onBlur={(e) => {
                    const value = e.target.value;
                    const page = parseInt(value);
                    if (value === '' || isNaN(page) || page < 1) {
                      setSelectedPageForMarking('1');
                    } else {
                      setSelectedPageForMarking(String(page));
                    }
                  }}
                  className="w-20 px-2 py-1 border border-border rounded text-sm"
                  min={1}
                />
                <button
                  onClick={() => {
                    if (!pdfPreviewUrl) {
                      onSpeak?.('PDF 파일을 먼저 선택해주세요.');
                      return;
                    }
                    setShowBboxMarker(true);
                  }}
                  className="px-3 py-1 text-sm bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors flex items-center gap-1"
                >
                  <ImageIcon className="w-4 h-4" />
                  영역 마킹
                </button>
              </div>

              {parsingGuideRegions.length > 0 && (
                <div className="mt-2">
                  <div className="text-xs font-medium mb-1">마킹된 영역 ({parsingGuideRegions.length}개):</div>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {parsingGuideRegions.map((region, idx) => (
                      <div key={idx} className="text-xs bg-secondary/50 rounded px-2 py-1">
                        페이지 {region.page}: {region.label}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleBack}
              className="flex-1 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 flex items-center justify-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              이전
            </button>
            <button
              onClick={handleSkipBbox}
              className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80"
            >
              건너뛰기
            </button>
            <button
              onClick={handleNext}
              className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 flex items-center justify-center gap-2"
            >
              다음
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {showBboxMarker && pdfPreviewUrl && (
          <PDFBboxMarker
            pdfUrl={pdfPreviewUrl}
            pageNumber={parseInt(selectedPageForMarking) || 1}
            existingRegions={parsingGuideRegions}
            onRegionsChange={setParsingGuideRegions}
            onClose={() => setShowBboxMarker(false)}
          />
        )}
      </div>
    );
  }

  // Step 5: TOC 입력
  if (step === 'toc') {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <button
            onClick={handleBack}
            className="p-1 hover:bg-secondary rounded"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <h2 className="text-xl font-bold">5단계: 목차(TOC) 텍스트 입력</h2>
        </div>

        <TOCInputStep
          tocPages={tocPages}
          tocText={tocText}
          tocLectureExamples={tocLectureExamples}
          tocNonLectureExamples={tocNonLectureExamples}
          expectedLectureCount={expectedLectureCount}
          extractedTextExamples={extractedTextExamples}
          extractingText={extractingText}
          extractingTocText={extractingTocText}
          cleaningTocText={cleaningTocText}
          customCleaningPrompt={customCleaningPrompt}
          onTocPagesChange={setTocPages}
          onTocTextChange={setTocText}
          onLectureExamplesChange={setTocLectureExamples}
          onNonLectureExamplesChange={setTocNonLectureExamples}
          onExpectedCountChange={setExpectedLectureCount}
          onExtractTocText={handleExtractTocText}
          onCleanTocText={handleCleanTocText}
          onExtractTextExamples={handleExtractTextExamples}
          onCustomCleaningPromptChange={setCustomCleaningPrompt}
        />

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-3 mt-4">
            <p className="text-error text-sm">{error}</p>
          </div>
        )}

        <div className="flex gap-2 mt-4">
          <button
            onClick={handleBack}
            className="flex-1 px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 flex items-center justify-center gap-2"
          >
            <ChevronLeft className="w-4 h-4" />
            이전
          </button>
          <button
            onClick={handleNext}
            disabled={generating}
            className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            {generating ? '템플릿 생성 중...' : '템플릿 생성 및 파싱 시작'}
          </button>
        </div>
      </div>
    );
  }

  // Step 5: 생성 중 또는 생성 완료
  if (step === 'generating') {
    // 템플릿 생성 완료 후 파싱 시작 화면
    if (generatedTemplate && !generating) {
      return (
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="w-6 h-6 text-green-500" />
            </div>
            <h2 className="text-xl font-bold mb-2">템플릿 생성 완료</h2>
            <p className="text-sm text-muted-foreground mb-4">
              템플릿이 성공적으로 생성되었습니다. 이제 PDF 파싱을 시작할 수 있습니다.
            </p>
            
            {generatedTemplate.warnings && generatedTemplate.warnings.length > 0 && (
              <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-4 text-left max-w-2xl mx-auto">
                <p className="text-sm font-medium text-yellow-700 dark:text-yellow-400 mb-2">경고:</p>
                <ul className="text-xs text-yellow-600 dark:text-yellow-300 space-y-1">
                  {generatedTemplate.warnings.map((warning, idx) => (
                    <li key={idx}>• {warning}</li>
                  ))}
                </ul>
              </div>
            )}

            {error && (
              <div className="bg-error/10 border border-error rounded-lg p-3 mb-4 max-w-2xl mx-auto">
                <p className="text-error text-sm">{error}</p>
              </div>
            )}

            <div className="flex gap-2 justify-center">
              <button
                onClick={handleBack}
                className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 flex items-center justify-center gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                이전
              </button>
              <button
                onClick={handleStartParsing}
                disabled={!file}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Upload className="w-4 h-4" />
                파싱 시작
              </button>
            </div>
          </div>
        </div>
      );
    }
    
    // 템플릿 생성 중 화면
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <h2 className="text-xl font-bold mb-2">템플릿 생성 중...</h2>
          <p className="text-sm text-muted-foreground">
            GPT가 템플릿을 생성하고 있습니다. 잠시만 기다려주세요.
          </p>
        </div>
      </div>
    );
  }

  // Step 6: 파싱 중
  if (step === 'parsing') {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <h2 className="text-xl font-bold mb-2">파싱 중...</h2>
          <p className="text-sm text-muted-foreground">
            PDF를 파싱하고 있습니다. 완료까지 1-2분 정도 걸립니다.
          </p>
        </div>
      </div>
    );
  }

  return null;
}
