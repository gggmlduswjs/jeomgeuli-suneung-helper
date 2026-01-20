/**
 * Unit 이미지 컴포넌트
 */
interface UnitImageProps {
  imagePath: string;
  alt: string;
}

export default function UnitImage({ imagePath, alt }: UnitImageProps) {
  const handleImageError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    console.error('이미지 로드 실패:', imagePath);
    (e.target as HTMLImageElement).style.display = 'none';
  };

  return (
    <div className="my-4">
      <img
        src={imagePath}
        alt={alt}
        className="w-full max-w-2xl mx-auto rounded-lg shadow-md"
        onError={handleImageError}
      />
    </div>
  );
}
