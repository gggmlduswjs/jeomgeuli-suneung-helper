/**
 * TOC(목차) 텍스트 → GPT 템플릿 생성 Wizard
 * - 관리자가 목차를 붙여넣으면 서버에서 템플릿(JSON)을 생성
 * - 생성된 템플릿을 TemplateEditor로 넘겨 검토/저장(생성) 가능
 */
import { useMemo, useState, useEffect } from 'react';
import { templatesAPI, type ParsingTemplate, type ParsingGuideRegion, type CurriculumStructureSurvey } from '../../services/templates';
import TemplateEditor from './TemplateEditor';
import PDFBboxMarker from './PDFBboxMarker';
import { ChevronLeft, Sparkles, Image as ImageIcon, Trash2 } from 'lucide-react';
import { useTOCAutoExtract } from '../../hooks/useTOCAutoExtract';

interface TOCTemplateWizardProps {
  onBack: () => void;
  onSaved?: () => void;
  onSpeak?: (message: string) => void;
}

export default function TOCTemplateWizard({ onBack, onSaved, onSpeak }: TOCTemplateWizardProps) {
  const [subject, setSubject] = useState<'literature' | 'math1' | 'english'>('literature');
  const [year, setYear] = useState<string>(String(new Date().getFullYear()));
  const [name, setName] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [tocText, setTocText] = useState<string>('');
  const [expectedLectureCount, setExpectedLectureCount] = useState<string>('');
  const [tocLectureExamplesText, setTocLectureExamplesText] = useState<string>('');
  const [tocNonLectureExamplesText, setTocNonLectureExamplesText] = useState<string>('');
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState<ParsingTemplate | null>(null);
  const [notes, setNotes] = useState<string[]>([]);
  const [curriculumSurvey, setCurriculumSurvey] = useState<CurriculumStructureSurvey>({
    is_lecture_based: true,
    lecture_units: ['concept', 'passage', 'problem'],
    unit_order: ['concept', 'passage', 'problem'],
  });
  const [parsingGuideRegions, setParsingGuideRegions] = useState<ParsingGuideRegion[]>([]);
  const [showBboxMarker, setShowBboxMarker] = useState(false);
  const [selectedPageForMarking, setSelectedPageForMarking] = useState<number>(1);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);
  const [extractingText, setExtractingText] = useState(false);
  const [extractedTextExamples, setExtractedTextExamples] = useState<{ [key: string]: string[] } | null>(null);
  const [samplePagesForExtraction, setSamplePagesForExtraction] = useState<string>('15,30,50');
  const [parsedLectures, setParsedLectures] = useState<Array<{
    lecture_id: number;
    title: string;
    start_page: number | null;
    end_page: number | null;
  }> | null>(null);
  const [parsingLectures, setParsingLectures] = useState(false);
  const [tocPages, setTocPages] = useState<string>('3,4,5');
  const [extractingTocText, setExtractingTocText] = useState(false);
  const [cleaningTocText, setCleaningTocText] = useState(false);

  const defaultName = useMemo(() => {
    const safeYear = year?.trim() || String(new Date().getFullYear());
    return `ebs_수능특강_${subject}_${safeYear}`;
  }, [subject, year]);

  // bbox 마킹 페이지가 변경되면 샘플 페이지 자동 업데이트
  useEffect(() => {
    if (parsingGuideRegions.length > 0) {
      // 마킹된 페이지 번호 추출 (중복 제거)
      const markedPages = [...new Set(parsingGuideRegions.map(r => r.page))];
      markedPages.sort((a, b) => a - b);
      setSamplePagesForExtraction(markedPages.join(','));
    }
  }, [parsingGuideRegions]);

  // TOC 텍스트 자동 분석
  useTOCAutoExtract(
    tocText,
    (result) => {
      // 자동으로 채우기 (사용자가 수동으로 입력한 경우는 덮어쓰지 않음)
      if (result.lectureLines.length > 0 && !tocLectureExamplesText.trim()) {
        setTocLectureExamplesText(result.lectureLines.join('\n'));
      }
      if (result.lectureCount > 0 && !expectedLectureCount.trim()) {
        setExpectedLectureCount(String(result.lectureCount));
      }
      if (result.nonLectureLines.length > 0 && !tocNonLectureExamplesText.trim()) {
        setTocNonLectureExamplesText(result.nonLectureLines.join('\n'));
      }
    },
    [tocLectureExamplesText, expectedLectureCount, tocNonLectureExamplesText]
  );

  const handleExtractTocText = async () => {
    if (!pdfFile) {
      onSpeak?.('먼저 PDF 파일을 업로드해주세요.');
      return;
    }

    if (!tocPages.trim()) {
      onSpeak?.('목차 페이지 번호를 입력해주세요 (예: 3,4,5).');
      return;
    }

    setExtractingTocText(true);
    try {
      const result = await templatesAPI.extractTocText(pdfFile, tocPages);
      setTocText(result.toc_text);

      const pageCount = result.pages_extracted.length;
      const lineCount = result.total_lines;

      if (lineCount === 0) {
        onSpeak?.('목차 텍스트를 추출하지 못했습니다. 페이지 번호를 확인해주세요.');
      } else {
        onSpeak?.(`${pageCount}개 페이지에서 ${lineCount}줄의 목차 텍스트를 추출했습니다. 검토 후 수정하세요.`);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '목차 텍스트 추출 중 오류가 발생했습니다.';
      onSpeak?.(message);
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
    try {
      const result = await templatesAPI.cleanTocText(tocText);
      setTocText(result.cleaned_text);

      onSpeak?.(`목차 텍스트를 정제했습니다. ${result.changes_made}`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '목차 텍스트 정제 중 오류가 발생했습니다.';
      onSpeak?.(message);
      console.error('목차 텍스트 정제 오류:', err);
    } finally {
      setCleaningTocText(false);
    }
  };

  const handleParseTocLectures = async () => {
    if (!tocText || tocText.trim().length < 20) {
      onSpeak?.('목차 텍스트를 먼저 입력해주세요.');
      return;
    }

    setParsingLectures(true);
    try {
      const result = await templatesAPI.parseTocLectures(tocText);
      setParsedLectures(result.lectures);

      const withPages = result.lectures_with_pages;
      const total = result.total_lectures;

      if (total === 0) {
        onSpeak?.('강의 목록을 추출하지 못했습니다. 목차 형식을 확인해주세요.');
      } else if (withPages === 0) {
        onSpeak?.(`${total}개 강의를 추출했지만 페이지 번호가 없습니다. 목차에 페이지 번호를 포함해주세요.`);
      } else if (withPages < total) {
        onSpeak?.(`${total}개 강의 중 ${withPages}개의 페이지 범위를 추출했습니다. 나머지는 수동으로 입력해주세요.`);
      } else {
        onSpeak?.(`${total}개 강의의 페이지 범위를 추출했습니다. 검토 후 수정하세요.`);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '강의 목록 추출 중 오류가 발생했습니다.';
      onSpeak?.(message);
      console.error('강의 목록 추출 오류:', err);
    } finally {
      setParsingLectures(false);
    }
  };

  const handleExtractTextExamples = async () => {
    if (!pdfFile) {
      onSpeak?.('먼저 PDF 파일을 업로드해주세요.');
      return;
    }

    // region_hints가 있는지 확인
    const regionHints: { [key: string]: { y_min: number; y_max: number } } = {};

    // 기본 region_hints 사용 (과목별)
    type RegionConfig = { [regionName: string]: { y_min: number; y_max: number } };
    const defaultRegionHints: { [subject: string]: RegionConfig } = {
      'literature': {
        'concept': { y_min: 0.11, y_max: 0.84 },
        'passage': { y_min: 0.12, y_max: 0.54 },
        'problem': { y_min: 0.10, y_max: 0.81 }
      },
      'math1': {
        'concept': { y_min: 0.10, y_max: 0.80 },
        'passage': { y_min: 0.15, y_max: 0.50 },
        'problem': { y_min: 0.12, y_max: 0.85 }
      },
      'english': {
        'concept': { y_min: 0.10, y_max: 0.75 },
        'passage': { y_min: 0.15, y_max: 0.55 },
        'problem': { y_min: 0.12, y_max: 0.80 }
      }
    };

    Object.assign(regionHints, defaultRegionHints[subject] || defaultRegionHints['literature']);

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
        pdfFile,
        subject,
        regionHints,
        pages,
        parsingGuideRegions.length > 0 ? parsingGuideRegions : undefined
      );

      setExtractedTextExamples(result.region_text_examples);

      // 결과에 따른 피드백
      const totalExamples = result.total_examples;
      if (totalExamples === 0) {
        onSpeak?.('텍스트를 추출하지 못했습니다. 다른 페이지를 시도해보세요.');
      } else if (totalExamples < 10) {
        onSpeak?.(`${result.pages_processed}개 페이지에서 ${totalExamples}개 텍스트 예시를 추출했습니다. 더 많은 예시를 원하면 다른 페이지를 추가하세요.`);
      } else {
        onSpeak?.(`${result.pages_processed}개 페이지에서 ${totalExamples}개 텍스트 예시를 추출했습니다.`);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '텍스트 추출 중 오류가 발생했습니다.';
      onSpeak?.(message);
    } finally {
      setExtractingText(false);
    }
  };

  const handleGenerate = async () => {
    const finalName = (name || defaultName).trim();
    const finalYear = year.trim();

    let lectureExamples = tocLectureExamplesText
      .split('\n')
      .map(s => s.trim())
      .filter(Boolean);
    const nonLectureExamples = tocNonLectureExamplesText
      .split('\n')
      .map(s => s.trim())
      .filter(Boolean);

    if (!tocText.trim() || tocText.trim().length < 20) {
      onSpeak?.('목차 텍스트를 더 붙여넣어주세요.');
      return;
    }
    
    // 자동 추출이 안 된 경우 다시 시도
    if (lectureExamples.length < 1) {
      const lines = tocText.split('\n').map(l => l.trim()).filter(Boolean);
      const lecturePattern = /(\d+)\s*강|강\s*(\d+)/i;
      for (const line of lines) {
        const match = lecturePattern.exec(line);
        if (match) {
          lectureExamples.push(line);
          if (lectureExamples.length >= 3) break;
        }
      }
    }
    
    if (lectureExamples.length < 1) {
      onSpeak?.('목차 텍스트에서 강의 라인을 찾을 수 없습니다. 수동으로 입력해주세요.');
      return;
    }
    
    // 강의 개수 자동 추출
    let finalExpectedCount = expectedLectureCount.trim();
    if (!finalExpectedCount || Number.isNaN(Number(finalExpectedCount))) {
      const lines = tocText.split('\n').map(l => l.trim()).filter(Boolean);
      const lecturePattern = /(\d+)\s*강|강\s*(\d+)/i;
      const lectureNumbers = new Set<number>();
      for (const line of lines) {
        const match = lecturePattern.exec(line);
        if (match) {
          const num = parseInt(match[1] || match[2], 10);
          if (!isNaN(num) && num > 0 && num < 200) {
            lectureNumbers.add(num);
          }
        }
      }
      if (lectureNumbers.size > 0) {
        finalExpectedCount = String(lectureNumbers.size);
        setExpectedLectureCount(finalExpectedCount);
      }
    }
    
    if (!finalExpectedCount || Number.isNaN(Number(finalExpectedCount))) {
      onSpeak?.('목차 기준 "강의 개수"를 숫자로 입력해주세요.');
      return;
    }

    setGenerating(true);
    setNotes([]);
    try {
      // 추출된 텍스트 예시가 있으면 defaults에 포함
      const defaultsWithTextExamples: Record<string, unknown> = {
        toc_end_page: 7,
        start_content_page: 8,
        paragraph_y_threshold: 25
      };

      if (extractedTextExamples && Object.keys(extractedTextExamples).length > 0) {
        defaultsWithTextExamples.region_text_examples = extractedTextExamples;
      }

      const res = await templatesAPI.generateFromToc({
        subject,
        name: finalName,
        version: finalYear,
        description: description.trim(),
        year: parseInt(year, 10) || undefined,
        book_name: description.trim() || undefined,
        toc_text: tocText,
        curriculum_survey: curriculumSurvey,
        parsing_guide_regions: parsingGuideRegions.length > 0 ? parsingGuideRegions : undefined,
        toc_lecture_line_examples: lectureExamples,
        toc_nonlecture_line_examples: nonLectureExamples,
        expected_lecture_count: parseInt(finalExpectedCount, 10),
        toc_lecture_list: parsedLectures || undefined, // 사용자가 편집한 강의 목록
        save: false,
        model_name: 'gpt-4o-mini',
        confidence: 0.85,
        defaults: defaultsWithTextExamples
      });

      const tpl = res.template as any;
      setNotes(Array.isArray(tpl._notes) ? tpl._notes : []);
      // TemplateEditor는 ParsingTemplate 타입만 받도록 _notes 제거
      const { _notes, ...clean } = tpl;
      setGenerated(clean as ParsingTemplate);
      onSpeak?.('템플릿 초안이 생성되었습니다. 검토 후 저장하세요.');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '알 수 없는 오류';
      onSpeak?.(message || '템플릿 생성 중 오류가 발생했습니다.');
    } finally {
      setGenerating(false);
    }
  };

  if (generated) {
    return (
      <div className="flex flex-col h-full">
        <div className="mb-3">
          <button
            onClick={() => setGenerated(null)}
            className="px-3 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2"
          >
            <ChevronLeft className="w-4 h-4" />
            목차 입력으로 돌아가기
          </button>
          {notes.length > 0 && (
            <div className="mt-2 text-xs text-muted-foreground bg-card border border-border rounded-lg p-3">
              <div className="font-medium mb-1">생성 메모</div>
              <ul className="list-disc pl-5 space-y-1">
                {notes.slice(0, 6).map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-hidden">
          <TemplateEditor
            template={generated}
            mode="create"
            onSave={() => {
              onSpeak?.('템플릿이 생성되었습니다.');
              onSaved?.();
            }}
            onCancel={() => setGenerated(null)}
            onSpeak={onSpeak}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="mb-4">
        <button
          onClick={onBack}
          className="mb-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2"
        >
          <ChevronLeft className="w-4 h-4" />
          뒤로가기
        </button>
        <h2 className="text-xl font-bold">목차로 템플릿 생성</h2>
        <p className="text-sm text-muted-foreground">목차 텍스트를 붙여넣고 GPT로 템플릿 초안을 만듭니다.</p>
      </div>

      <div className="space-y-4">
        {/* 1. 기본 정보 */}
        <div className="border border-border rounded-lg p-4 bg-card">
          <h3 className="text-base font-semibold mb-3">1. 기본 정보</h3>

          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-sm font-medium mb-1">과목</label>
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value as any)}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            >
              <option value="literature">문학</option>
              <option value="math1">수학</option>
              <option value="english">영어</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">버전(연도)</label>
            <input
              type="text"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background"
              placeholder="예: 2026"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">템플릿 이름</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            placeholder={defaultName}
          />
          <p className="mt-1 text-xs text-muted-foreground">비워두면 기본값: {defaultName}</p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">설명(선택)</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            placeholder="예: 2026 수능특강 문학 TOC 기반 템플릿"
          />
        </div>
          </div>
        </div>

        {/* 2. 커리큘럼 구조 설문 */}
        <div className="border border-border rounded-lg p-4 bg-card">
          <h3 className="text-base font-semibold mb-3">2. 커리큘럼 구조 설문 (선택)</h3>
          <div className="space-y-3">
            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={curriculumSurvey.is_lecture_based}
                  onChange={(e) => setCurriculumSurvey(prev => ({ ...prev, is_lecture_based: e.target.checked }))}
                  className="w-4 h-4"
                />
                <span className="text-sm">강의 기반 구조</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">단위 순서</label>
              <input
                type="text"
                value={curriculumSurvey.unit_order.join(', ')}
                onChange={(e) => {
                  const units = e.target.value.split(',').map(s => s.trim()).filter(Boolean);
                  if (units.length > 0) {
                    setCurriculumSurvey(prev => ({ ...prev, unit_order: units }));
                  }
                }}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm"
                placeholder="concept, passage, problem"
              />
              <p className="mt-1 text-xs text-muted-foreground">쉼표로 구분하여 입력 (예: concept, passage, problem)</p>
            </div>
          </div>
        </div>

        {/* 3. PDF 업로드 */}
        <div className="border border-border rounded-lg p-4 bg-card">
          <h3 className="text-base font-semibold mb-3">3. PDF 업로드 (필수)</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1">PDF 파일</label>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    setPdfFile(file);
                    const url = URL.createObjectURL(file);
                    setPdfPreviewUrl(url);
                    // PDF 변경 시 추출된 텍스트 초기화
                    setExtractedTextExamples(null);
                  }
                }}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                PDF를 업로드하면 영역별 텍스트 예시를 자동으로 추출할 수 있습니다.
              </p>
            </div>

            {pdfFile && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-1">샘플 페이지 (쉼표로 구분)</label>
                  <input
                    type="text"
                    value={samplePagesForExtraction}
                    onChange={(e) => setSamplePagesForExtraction(e.target.value)}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm"
                    placeholder="15,30,50"
                  />
                  {parsingGuideRegions.length > 0 ? (
                    <p className="mt-1 text-xs text-green-600 dark:text-green-400">
                      ✅ 영역 마킹한 페이지로 자동 설정됨 ({parsingGuideRegions.length}개 영역)
                    </p>
                  ) : (
                    <p className="mt-1 text-xs text-muted-foreground">
                      💡 <strong>팁:</strong> 본문 내용이 있는 페이지를 선택하세요 (목차/표지 제외). 예: 15,30,50
                    </p>
                  )}
                </div>

                <button
                  onClick={handleExtractTextExamples}
                  disabled={extractingText}
                  className="w-full px-3 py-2 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors flex items-center justify-center gap-2 font-medium disabled:opacity-50"
                >
                  <Sparkles className="w-4 h-4" />
                  {extractingText ? '추출 중...' : '텍스트 예시 자동 추출'}
                </button>
              </>
            )}

            {/* 추출된 텍스트 예시 표시 */}
            {extractedTextExamples && (
              <div className="mt-3 border-t border-border pt-3">
                <div className="text-sm font-medium mb-2">추출된 텍스트 예시 (수정 가능):</div>
                <div className="space-y-2">
                  {Object.entries(extractedTextExamples).map(([regionType, texts]) => (
                    <div key={regionType} className="bg-secondary/50 rounded p-2">
                      <div className="text-xs font-medium mb-1 text-primary">{regionType} ({texts.length}개)</div>
                      <div className="text-xs space-y-1 max-h-32 overflow-y-auto">
                        {texts.slice(0, 10).map((text, idx) => (
                          <div key={idx} className="text-muted-foreground truncate" title={text}>
                            {text}
                          </div>
                        ))}
                        {texts.length > 10 && (
                          <div className="text-muted-foreground italic">... 외 {texts.length - 10}개</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  ✅ 이 텍스트 예시들이 템플릿 생성 시 자동으로 포함됩니다.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* 4. 영역 마킹 (고급, 선택) */}
        <details className="border border-border rounded-lg p-4 bg-card">
          <summary className="text-base font-semibold cursor-pointer hover:text-primary transition-colors">
            4. 영역 마킹 (고급, 선택)
          </summary>
          <div className="mt-3 space-y-2">
            <div className="flex items-center justify-end mb-2">
              <button
                onClick={() => {
                  if (!pdfFile) {
                    onSpeak?.('먼저 PDF 파일을 선택해주세요.');
                    return;
                  }
                  setShowBboxMarker(true);
                }}
                className="px-3 py-1 text-xs bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors flex items-center gap-1"
              >
                <ImageIcon className="w-3 h-3" />
                영역 마킹
              </button>
            </div>
            <p className="text-xs text-muted-foreground">
              3-5개 대표 페이지에 개념/본문/문제 영역을 직접 마킹하여 더 정확한 좌표 범위를 설정할 수 있습니다.
            </p>
            <div>
              <label className="block text-sm font-medium mb-1">PDF 파일</label>
              <p className="text-xs text-muted-foreground">
                위에서 업로드한 PDF 파일: {pdfFile?.name || '없음'}
              </p>
            </div>
            {pdfFile && (
              <div>
                <label className="block text-sm font-medium mb-1">마킹할 페이지 번호</label>
                <input
                  type="number"
                  value={selectedPageForMarking}
                  onChange={(e) => {
                    const page = parseInt(e.target.value);
                    if (!isNaN(page) && page >= 1) {
                      setSelectedPageForMarking(page);
                    } else if (e.target.value === '') {
                      setSelectedPageForMarking(1);
                    }
                  }}
                  onBlur={(e) => {
                    if (e.target.value === '' || parseInt(e.target.value) < 1) {
                      setSelectedPageForMarking(1);
                    }
                  }}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm"
                  min={1}
                  placeholder="1"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  마킹할 PDF 페이지 번호를 입력하세요.
                </p>
              </div>
            )}
            {parsingGuideRegions.length > 0 && (
              <div className="mt-2">
                <div className="text-xs font-medium mb-1">마킹된 영역 ({parsingGuideRegions.length}개):</div>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {parsingGuideRegions.map((region, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs bg-secondary/50 rounded px-2 py-1">
                      <span>
                        페이지 {region.page}: {region.label} ({region.bbox[0]}, {region.bbox[1]}, {region.bbox[2]}, {region.bbox[3]})
                      </span>
                      <button
                        onClick={() => {
                          setParsingGuideRegions(prev => prev.filter((_, i) => i !== idx));
                        }}
                        className="text-danger hover:text-danger/80"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </details>

        {/* 5. 목차 입력 */}
        <div className="border border-border rounded-lg p-4 bg-card">
          <h3 className="text-base font-semibold mb-4">5. 목차 입력</h3>

          <div className="space-y-4">
            {/* 5-1. 목차 페이지 번호 입력 및 텍스트 추출 */}
            <div>
              <label className="block text-sm font-medium mb-2">
                목차 페이지 번호 (쉼표로 구분)
              </label>
              <input
                type="text"
                value={tocPages}
                onChange={(e) => setTocPages(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm"
                placeholder="3,4,5"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                목차가 있는 PDF 페이지 번호를 입력하세요 (예: 3,4,5)
              </p>

              <button
                onClick={handleExtractTocText}
                disabled={extractingTocText || !pdfFile}
                className="w-full mt-2 px-4 py-3 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors flex items-center justify-center gap-2 font-medium disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                {extractingTocText ? '추출 중...' : 'PDF에서 목차 텍스트 추출'}
              </button>
            </div>

            {/* 5-2. 추출된 목차 텍스트 표시 및 편집 */}
            <div>
              <label className="block text-sm font-medium mb-2">
                목차 텍스트 (검토 및 수정)
              </label>
              <textarea
                value={tocText}
                onChange={(e) => setTocText(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background font-mono text-sm"
                rows={12}
                placeholder="위 버튼을 클릭하여 목차 텍스트를 자동으로 추출하거나, 직접 붙여넣으세요.&#10;&#10;예시:&#10;1강 | 시의 표현과 형식&#10;해 (박두진) 009&#10;2강 | 시의 내용&#10;..."
              />
              <p className="mt-1 text-xs text-muted-foreground">
                추출된 텍스트가 올바른지 확인하고 필요시 수정하세요.
              </p>

              {/* AI로 목차 텍스트 정제 버튼 */}
              {tocText.trim().length > 20 && (
                <button
                  onClick={handleCleanTocText}
                  disabled={cleaningTocText}
                  className="w-full mt-2 px-4 py-2 bg-gradient-to-r from-purple-500/10 to-blue-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 rounded-lg hover:from-purple-500/20 hover:to-blue-500/20 transition-colors flex items-center justify-center gap-2 font-medium disabled:opacity-50"
                >
                  <Sparkles className="w-4 h-4" />
                  {cleaningTocText ? 'AI 정제 중...' : 'AI로 목차 텍스트 정제 (OCR 오류 수정)'}
                </button>
              )}
            </div>

            {/* 5-3. 강의 목록 분석 버튼 */}
            <button
              onClick={handleParseTocLectures}
              disabled={parsingLectures || !tocText.trim()}
              className="w-full px-4 py-3 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors flex items-center justify-center gap-2 font-medium disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              {parsingLectures ? '분석 중...' : '목차에서 강의 목록 및 페이지 범위 추출'}
            </button>
          </div>
        </div>

        {/* 6. 추출된 강의 목록 검토 및 수정 */}
        {parsedLectures && parsedLectures.length > 0 && (
          <div className="border border-border rounded-lg p-4 bg-card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-semibold">
                6. 강의 목록 검토 및 수정 ({parsedLectures.length}개)
              </h3>
              <button
                onClick={() => setParsedLectures(null)}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                초기화
              </button>
            </div>

            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-xs border-collapse">
                <thead className="sticky top-0 bg-card border-b border-border">
                  <tr>
                    <th className="px-2 py-2 text-left w-16">강의</th>
                    <th className="px-2 py-2 text-left">제목</th>
                    <th className="px-2 py-2 text-left w-24">시작 페이지</th>
                    <th className="px-2 py-2 text-left w-24">종료 페이지</th>
                  </tr>
                </thead>
                <tbody>
                  {parsedLectures.map((lecture, idx) => (
                    <tr key={idx} className="border-b border-border hover:bg-secondary/30">
                      <td className="px-2 py-2 font-medium">{lecture.lecture_id}강</td>
                      <td className="px-2 py-2">
                        <input
                          type="text"
                          value={lecture.title}
                          onChange={(e) => {
                            const updated = [...parsedLectures];
                            updated[idx].title = e.target.value;
                            setParsedLectures(updated);
                          }}
                          className="w-full px-2 py-1 border border-border rounded bg-background text-xs"
                        />
                      </td>
                      <td className="px-2 py-2">
                        <input
                          type="number"
                          value={lecture.start_page ?? ''}
                          onChange={(e) => {
                            const updated = [...parsedLectures];
                            updated[idx].start_page = e.target.value ? parseInt(e.target.value) : null;
                            setParsedLectures(updated);
                          }}
                          className="w-full px-2 py-1 border border-border rounded bg-background text-xs"
                          placeholder="-"
                        />
                      </td>
                      <td className="px-2 py-2">
                        <input
                          type="number"
                          value={lecture.end_page ?? ''}
                          onChange={(e) => {
                            const updated = [...parsedLectures];
                            updated[idx].end_page = e.target.value ? parseInt(e.target.value) : null;
                            setParsedLectures(updated);
                          }}
                          className="w-full px-2 py-1 border border-border rounded bg-background text-xs"
                          placeholder="끝까지"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="mt-3 text-xs text-muted-foreground">
              💡 <strong>팁:</strong> 강의 제목과 페이지 범위를 수정할 수 있습니다. 종료 페이지가 비어있으면 다음 강의 시작 전까지입니다.
            </p>
          </div>
        )}

        {/* 자동 추출된 정보 (접을 수 있게) */}
        <details className="border border-border rounded-lg p-3 bg-card">
          <summary className="text-sm font-medium cursor-pointer hover:text-primary transition-colors">
            자동 추출된 정보 (수정 가능)
          </summary>
          <div className="mt-3 space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-sm font-medium mb-1">목차 기준 강의 개수</label>
                <input
                  type="number"
                  value={expectedLectureCount}
                  onChange={(e) => setExpectedLectureCount(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-sm"
                  placeholder="자동 추출됨"
                  min={1}
                />
                <p className="mt-1 text-xs text-muted-foreground">파싱 시 강의목록 검증에 사용됩니다.</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">TOC 강의 라인 예시</label>
                <textarea
                  value={tocLectureExamplesText}
                  onChange={(e) => setTocLectureExamplesText(e.target.value)}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background font-mono text-xs"
                  rows={3}
                  placeholder="자동 추출됨"
                />
                <p className="mt-1 text-xs text-muted-foreground">강의 라인 예시 (3-5줄 권장)</p>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">TOC 비강의 라인 예시 (선택)</label>
              <textarea
                value={tocNonLectureExamplesText}
                onChange={(e) => setTocNonLectureExamplesText(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg bg-background font-mono text-xs"
                rows={2}
                placeholder="자동 추출됨 (부록, 해설 등)"
              />
              <p className="mt-1 text-xs text-muted-foreground">강의가 아닌 줄을 넣으면 과매칭을 줄일 수 있습니다.</p>
            </div>
          </div>
        </details>

        <button
          onClick={handleGenerate}
          disabled={generating}
          className="w-full px-4 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 font-medium disabled:opacity-50"
        >
          <Sparkles className="w-5 h-5" />
          {generating ? '생성 중...' : 'GPT로 템플릿 생성'}
        </button>
      </div>

      {/* Bbox 마킹 모달 */}
      {showBboxMarker && pdfPreviewUrl && (
        <PDFBboxMarker
          pdfUrl={pdfPreviewUrl}
          pageNumber={selectedPageForMarking}
          existingRegions={parsingGuideRegions}
          onRegionsChange={setParsingGuideRegions}
          onClose={() => setShowBboxMarker(false)}
        />
      )}
    </div>
  );
}

