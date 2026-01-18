import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShellMobile from '../../components/ui/AppShellMobile';
import SpeechBar from '../../components/input/SpeechBar';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import { curriculumAPI } from '../../services/curriculum';
import type { Subject } from '../../types/curriculum';

export default function CurriculumCreatePage() {
  const navigate = useNavigate();
  const { speak } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState<Subject>('KOREAN');
  const [hwpFiles, setHwpFiles] = useState<File[]>([]);
  const [pdfFile, setPdfFile] = useState<File | undefined>(undefined);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleHWPFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const hwpFiles = files.filter((f) => f.name.toLowerCase().endsWith('.hwp'));
    setHwpFiles((prev) => [...prev, ...hwpFiles]);
  };

  const handlePDFFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.name.toLowerCase().endsWith('.pdf')) {
      setPdfFile(file);
    }
  };

  const handleSubmit = async () => {
    if (!title || hwpFiles.length === 0) {
      const errorMsg = '제목과 한글 파일을 입력해주세요.';
      setError(errorMsg);
      speak(errorMsg);
      return;
    }

    setUploading(true);
    setError(null);
    speak('커리큘럼을 생성하고 있습니다. 잠시만 기다려주세요.');

    try {
      const result = await curriculumAPI.generate(subject, title, hwpFiles, pdfFile);
      speak('커리큘럼 생성이 시작되었습니다.');
      navigate(`/curriculum/${result.curriculum_id}`);
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || '커리큘럼 생성에 실패했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <AppShellMobile title="커리큘럼 생성" className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4 space-y-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-semibold mb-4">기본 정보</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">과목</label>
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value as Subject)}
                className="w-full px-3 py-2 border border-border rounded-lg"
                disabled={uploading}
              >
                <option value="KOREAN">문학</option>
                <option value="MATH">수1</option>
                <option value="ENGLISH">영어</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">교재명</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="예: 2026 수능특강 문학"
                className="w-full px-3 py-2 border border-border rounded-lg"
                disabled={uploading}
              />
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-semibold mb-4">강의대본 업로드</h3>
          <input
            type="file"
            accept=".hwp,.HWP"
            multiple
            onChange={handleHWPFileSelect}
            className="hidden"
            id="hwp-files"
            disabled={uploading}
          />
          <label
            htmlFor="hwp-files"
            className="block w-full py-3 px-4 border border-border rounded-lg text-center cursor-pointer hover:bg-muted"
          >
            HWP 파일 선택
          </label>
          {hwpFiles.length > 0 && (
            <div className="mt-4 space-y-2">
              {hwpFiles.map((file, index) => (
                <div key={index} className="text-sm text-muted">
                  • {file.name}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-card border border-border rounded-lg p-4">
          <h3 className="font-semibold mb-4">PDF 파일 (선택)</h3>
          <input
            type="file"
            accept=".pdf,.PDF"
            onChange={handlePDFFileSelect}
            className="hidden"
            id="pdf-file"
            disabled={uploading}
          />
          <label
            htmlFor="pdf-file"
            className="block w-full py-3 px-4 border border-border rounded-lg text-center cursor-pointer hover:bg-muted"
          >
            PDF 파일 선택
          </label>
          {pdfFile && (
            <div className="mt-4 text-sm text-muted">
              • {pdfFile.name}
            </div>
          )}
        </div>

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-4">
            <p className="text-error text-sm">{error}</p>
          </div>
        )}

        <div className="flex gap-2">
          <button
            onClick={handleSubmit}
            disabled={uploading || !title || hwpFiles.length === 0}
            className="flex-1 btn-primary"
          >
            {uploading ? '생성 중...' : '커리큘럼 생성'}
          </button>
          <button
            onClick={() => navigate('/curriculum')}
            className="btn-ghost"
            disabled={uploading}
          >
            취소
          </button>
        </div>
      </div>
    </AppShellMobile>
  );
}
