import { useRef, useState } from 'react';

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  onSpeak: (text: string) => void;
}

export default function ImageUpload({ onImageSelect, onSpeak }: ImageUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type.startsWith('image/')) {
        onImageSelect(file);
        
        // 미리보기 생성
        const reader = new FileReader();
        reader.onloadend = () => {
          setPreview(reader.result as string);
        };
        reader.readAsDataURL(file);
        
        onSpeak('이미지가 선택되었습니다. 분석을 시작합니다.');
      } else {
        onSpeak('이미지 파일만 업로드할 수 있습니다.');
      }
    }
  };

  const handleCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      // TODO: 카메라 스트림 처리
      onSpeak('카메라 기능은 곧 제공됩니다. 파일을 선택해주세요.');
      stream.getTracks().forEach(track => track.stop());
    } catch (err) {
      onSpeak('카메라 접근 권한이 필요합니다.');
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">그래프/도표 이미지 업로드</h3>
      
      <div className="flex gap-2">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
          aria-label="이미지 파일 선택"
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          className="btn-primary flex-1"
          aria-label="파일 선택"
        >
          파일 선택
        </button>
        <button
          onClick={handleCamera}
          className="btn-accent flex-1"
          aria-label="카메라로 촬영"
        >
          카메라
        </button>
      </div>

      {preview && (
        <div className="mt-4">
          <img
            src={preview}
            alt="업로드된 이미지"
            className="max-w-full h-auto rounded-lg border border-border"
            aria-label="업로드된 그래프 또는 도표"
          />
        </div>
      )}
    </div>
  );
}


