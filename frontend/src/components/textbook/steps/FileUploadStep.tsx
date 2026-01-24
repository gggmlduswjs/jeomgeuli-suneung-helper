/**
 * 파일 업로드 스텝
 * PDF 파일 선택 및 기본 정보 입력
 */
import { Upload } from 'lucide-react';
import { Subject } from '../../../types/book';

interface FileUploadStepProps {
  file: File | null;
  title: string;
  subject: Subject;
  year: number;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onTitleChange: (title: string) => void;
  onSubjectChange: (subject: Subject) => void;
  onYearChange: (year: number) => void;
  error: string | null;
}

export default function FileUploadStep({
  file,
  title,
  subject,
  year,
  onFileChange,
  onTitleChange,
  onSubjectChange,
  onYearChange,
  error
}: FileUploadStepProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">1. PDF 파일 업로드</h3>
        <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
          <input
            type="file"
            accept="application/pdf"
            onChange={onFileChange}
            className="hidden"
            id="pdf-upload"
          />
          <label
            htmlFor="pdf-upload"
            className="cursor-pointer flex flex-col items-center gap-3"
          >
            <Upload className="w-12 h-12 text-muted-foreground" />
            <div>
              <p className="text-sm font-medium">
                {file ? file.name : 'PDF 파일을 선택하세요'}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                클릭하여 파일 선택
              </p>
            </div>
          </label>
        </div>
        {error && (
          <p className="text-sm text-red-500 mt-2">{error}</p>
        )}
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">제목</label>
          <input
            type="text"
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            placeholder="교재 제목"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">과목</label>
          <select
            value={subject}
            onChange={(e) => onSubjectChange(e.target.value as Subject)}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background"
          >
            <option value={Subject.KOREAN}>국어 (문학)</option>
            <option value={Subject.ENGLISH}>영어</option>
            <option value={Subject.MATH}>수학</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">연도</label>
          <input
            type="number"
            value={year}
            onChange={(e) => onYearChange(parseInt(e.target.value) || new Date().getFullYear())}
            className="w-full px-3 py-2 border border-border rounded-lg bg-background"
            min="2020"
            max="2030"
          />
        </div>
      </div>
    </div>
  );
}
