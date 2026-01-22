/**
 * Unit 이미지 컴포넌트
 */
interface UnitImageProps {
  imagePath: string;
  alt: string;
}

export default function UnitImage({ imagePath, alt }: UnitImageProps) {
  // 이미지 경로 정규화 (상대 경로 처리)
  const normalizedPath = imagePath.startsWith('/') 
    ? imagePath 
    : imagePath.startsWith('http') 
      ? imagePath 
      : `/api/data/${imagePath}`;

  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    console.error('[UnitImage] 이미지 로드 실패:', normalizedPath);
    (e.target as HTMLImageElement).style.display = 'none';
    const placeholder = (e.target as HTMLImageElement).nextElementSibling as HTMLElement;
    if (placeholder) placeholder.style.display = 'flex';
  };

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    (e.target as HTMLImageElement).style.opacity = '1';
    const placeholder = (e.target as HTMLImageElement).nextElementSibling as HTMLElement;
    if (placeholder) placeholder.style.display = 'none';
  };

  return (
    <div className="my-4 relative min-h-[200px]">
      <img
        src={normalizedPath}
        alt={alt}
        className="w-full max-w-2xl mx-auto rounded-lg shadow-md"
        loading="eager" // 즉시 로드
        decoding="async" // 비동기 디코딩
        onLoad={handleImageLoad}
        onError={handleImageError}
        style={{ opacity: 0, transition: 'opacity 0.3s' }}
      />
      {/* 로딩 플레이스홀더 */}
      <div className="absolute inset-0 flex items-center justify-center bg-muted/50">
        <p className="text-muted-foreground text-sm">이미지 로딩 중...</p>
      </div>
    </div>
  );
}
