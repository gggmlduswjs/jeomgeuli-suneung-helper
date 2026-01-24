/**
 * 교재 PDF 업로드 컴포넌트 (AI 옵션 포함)
 */
import { useState } from 'react';
import { booksAPI } from '../../services/api/client';
import type { Book, AIProcessingOptions } from '../../types/book';
import { Subject } from '../../types/book';

interface BookUploadProps {
  onUploadComplete: (book: Book) => void;
  onSpeak?: (text: string) => void;
}

export default function BookUpload({ onUploadComplete, onSpeak }: BookUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState<Subject>(Subject.KOREAN);
  const [year, setYear] = useState<number>(new Date().getFullYear());
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // AI 처리 옵션
  const [showAIOptions, setShowAIOptions] = useState(false);
  const [aiOptions, setAIOptions] = useState<AIProcessingOptions>({
    // Level 1: ML (기본 활성화)
    enable_ml_deduplication: true,
    enable_ml_classification: true,

    // Level 2: DL (선택적)
    enable_layout_analysis: false,
    enable_math_recognition: false,

    // Level 3: LLM (선택적, API 키 필요)
    enable_llm_metadata: false,
    enable_llm_explanations: false,
    enable_llm_recommendations: false,
    openai_api_key: '',
    education_level: 'high',
  });

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

      // 파일명에서 제목 추출 (확장자 제거)
      const fileName = selectedFile.name.replace(/\.pdf$/i, '');
      if (!title) {
        setTitle(fileName);
      }
    }
  };

  const handleAIOptionChange = (key: keyof AIProcessingOptions, value: string | boolean) => {
    setAIOptions(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      setError('파일을 선택해주세요.');
      onSpeak?.('파일을 선택해주세요.');
      return;
    }

    if (!title.trim()) {
      setError('제목을 입력해주세요.');
      onSpeak?.('제목을 입력해주세요.');
      return;
    }

    // Level 3 (LLM) 옵션 활성화 시 API 키 확인
    const llmEnabled = aiOptions.enable_llm_metadata ||
                       aiOptions.enable_llm_explanations ||
                       aiOptions.enable_llm_recommendations;

    if (llmEnabled && !aiOptions.openai_api_key?.trim()) {
      setError('Level 3 (LLM) 기능을 사용하려면 OpenAI API 키를 입력해주세요.');
      onSpeak?.('Level 3 LLM 기능을 사용하려면 OpenAI API 키를 입력해주세요.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const book = await booksAPI.upload(file, title, subject, year, aiOptions);
      onSpeak?.(`${book.title} 업로드가 완료되었습니다.`);
      onUploadComplete(book);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '업로드 중 오류가 발생했습니다.';
      setError(errorMsg);
      onSpeak?.(errorMsg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4">교재 PDF 업로드</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">PDF 파일</label>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="w-full p-2 border border-border rounded-lg"
            disabled={uploading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">제목</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border border-border rounded-lg"
            placeholder="예: 문학 교재"
            disabled={uploading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">과목</label>
          <select
            value={subject}
            onChange={(e) => setSubject(e.target.value as Subject)}
            className="w-full p-2 border border-border rounded-lg"
            disabled={uploading}
          >
            <option value={Subject.KOREAN}>국어</option>
            <option value={Subject.ENGLISH}>영어</option>
            <option value={Subject.MATH}>수학</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">연도</label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(parseInt(e.target.value) || new Date().getFullYear())}
            className="w-full p-2 border border-border rounded-lg"
            min="2020"
            max="2030"
            disabled={uploading}
          />
        </div>

        {/* AI 처리 옵션 토글 */}
        <div className="border-t border-border pt-4">
          <button
            type="button"
            onClick={() => setShowAIOptions(!showAIOptions)}
            className="flex items-center justify-between w-full text-left font-medium text-sm"
            disabled={uploading}
          >
            <span>🤖 AI 처리 옵션 {showAIOptions ? '▼' : '▶'}</span>
            <span className="text-xs text-muted-foreground">
              (기본: Level 1 ML 활성화)
            </span>
          </button>
        </div>

        {showAIOptions && (
          <div className="bg-muted/30 rounded-lg p-4 space-y-4">
            {/* Level 1: ML */}
            <div className="space-y-2">
              <h3 className="font-semibold text-sm">Level 1: ML (기본)</h3>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={aiOptions.enable_ml_deduplication}
                  onChange={(e) => handleAIOptionChange('enable_ml_deduplication', e.target.checked)}
                  disabled={uploading}
                  className="rounded"
                />
                <span className="text-sm">중복 콘텐츠 제거</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={aiOptions.enable_ml_classification}
                  onChange={(e) => handleAIOptionChange('enable_ml_classification', e.target.checked)}
                  disabled={uploading}
                  className="rounded"
                />
                <span className="text-sm">하이브리드 블록 분류</span>
              </label>
            </div>

            {/* Level 2: DL */}
            <div className="space-y-2 border-t border-border pt-2">
              <h3 className="font-semibold text-sm">Level 2: Deep Learning (선택적)</h3>
              <p className="text-xs text-muted-foreground">처리 시간이 증가할 수 있습니다.</p>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={aiOptions.enable_layout_analysis}
                  onChange={(e) => handleAIOptionChange('enable_layout_analysis', e.target.checked)}
                  disabled={uploading}
                  className="rounded"
                />
                <span className="text-sm">문서 구조 분석 (LayoutLMv3)</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={aiOptions.enable_math_recognition}
                  onChange={(e) => handleAIOptionChange('enable_math_recognition', e.target.checked)}
                  disabled={uploading}
                  className="rounded"
                />
                <span className="text-sm">수식 인식 (TrOCR)</span>
              </label>
            </div>

            {/* Level 3: LLM */}
            <div className="space-y-2 border-t border-border pt-2">
              <h3 className="font-semibold text-sm">Level 3: LLM / GenAI (선택적)</h3>
              <p className="text-xs text-muted-foreground text-warning">
                ⚠️ OpenAI API 키가 필요하며, API 사용 비용이 발생합니다.
              </p>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={aiOptions.enable_llm_metadata}
                  onChange={(e) => handleAIOptionChange('enable_llm_metadata', e.target.checked)}
                  disabled={uploading}
                  className="rounded"
                />
                <span className="text-sm">메타데이터 자동 생성 (태그, 키워드)</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={aiOptions.enable_llm_explanations}
                  onChange={(e) => handleAIOptionChange('enable_llm_explanations', e.target.checked)}
                  disabled={uploading}
                  className="rounded"
                />
                <span className="text-sm">개념 설명 자동 생성</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={aiOptions.enable_llm_recommendations}
                  onChange={(e) => handleAIOptionChange('enable_llm_recommendations', e.target.checked)}
                  disabled={uploading}
                  className="rounded"
                />
                <span className="text-sm">유사 콘텐츠 추천 시스템 (RAG)</span>
              </label>

              {/* OpenAI API Key */}
              {(aiOptions.enable_llm_metadata ||
                aiOptions.enable_llm_explanations ||
                aiOptions.enable_llm_recommendations) && (
                <div className="mt-2">
                  <label className="block text-xs font-medium mb-1">OpenAI API 키</label>
                  <input
                    type="password"
                    value={aiOptions.openai_api_key || ''}
                    onChange={(e) => handleAIOptionChange('openai_api_key', e.target.value)}
                    className="w-full p-2 border border-border rounded text-sm"
                    placeholder="sk-..."
                    disabled={uploading}
                  />
                </div>
              )}

              {/* Education Level */}
              {aiOptions.enable_llm_explanations && (
                <div className="mt-2">
                  <label className="block text-xs font-medium mb-1">교육 수준</label>
                  <select
                    value={aiOptions.education_level}
                    onChange={(e) => handleAIOptionChange('education_level', e.target.value)}
                    className="w-full p-2 border border-border rounded text-sm"
                    disabled={uploading}
                  >
                    <option value="elementary">초등</option>
                    <option value="middle">중등</option>
                    <option value="high">고등</option>
                    <option value="university">대학</option>
                  </select>
                </div>
              )}
            </div>
          </div>
        )}

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-3">
            <p className="text-error text-sm">{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={uploading || !file}
          className="w-full px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? '업로드 및 AI 처리 중...' : '업로드'}
        </button>

        {uploading && (
          <p className="text-xs text-center text-muted-foreground">
            AI 처리가 활성화되어 있으면 처리 시간이 더 걸릴 수 있습니다.
          </p>
        )}
      </form>
    </div>
  );
}
