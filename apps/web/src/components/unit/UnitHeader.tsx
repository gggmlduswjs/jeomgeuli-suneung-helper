/**
 * Unit 헤더 컴포넌트
 */
interface UnitHeaderProps {
  title: string;
  textbookTitle?: string;
}

export default function UnitHeader({ title, textbookTitle }: UnitHeaderProps) {
  return (
    <div>
      <h2 className="text-xl font-bold mb-2">{title}</h2>
      {textbookTitle && (
        <p className="text-sm text-muted">교재: {textbookTitle}</p>
      )}
    </div>
  );
}
