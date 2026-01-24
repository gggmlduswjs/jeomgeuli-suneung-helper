/**
 * PDF 관리 카드
 * 교재 목록 및 업로드
 */
import { useNavigate } from 'react-router-dom';
import { Upload, BookOpen, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import type { Book, ParseStatus } from '../../types/book';

interface PDFManagementCardProps {
  books: Book[];
  onBookSelect?: (book: Book) => void;
}

export default function PDFManagementCard({
  books,
  onBookSelect,
}: PDFManagementCardProps) {
  const navigate = useNavigate();

  const getStatusIcon = (status: ParseStatus) => {
    switch (status) {
      case 'DONE':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'PROCESSING':
      case 'PENDING':
        return <Clock className="w-5 h-5 text-yellow-600" />;
      case 'FAILED':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <BookOpen className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: ParseStatus) => {
    switch (status) {
      case 'DONE':
        return '완료';
      case 'PROCESSING':
        return '파싱 중';
      case 'PENDING':
        return '대기 중';
      case 'FAILED':
        return '실패';
      default:
        return '알 수 없음';
    }
  };

  const handleBookClick = (book: Book) => {
    if (onBookSelect) {
      onBookSelect(book);
    } else {
      navigate(`/book/${book.book_id}`);
    }
  };

  const handleUploadClick = () => {
    navigate('/book');
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-3 border-2 border-gray-200">
      <div className="flex items-center justify-between mb-2.5">
        <h3 className="text-base font-semibold text-gray-800">교재 관리</h3>
        <button
          onClick={handleUploadClick}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          <Upload className="w-3.5 h-3.5" />
          <span>업로드</span>
        </button>
      </div>

      {books.length > 0 ? (
        <div className="space-y-2">
          {/* 최신 교재 1개만 표시 */}
          {(() => {
            const latestBook = books[0];
            return (
              <button
                key={latestBook.book_id}
                onClick={() => handleBookClick(latestBook)}
                className="w-full flex items-center justify-between p-2.5 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-left"
              >
                <div className="flex items-center gap-2.5 flex-1 min-w-0">
                  {getStatusIcon(latestBook.parse_status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">
                      {latestBook.title}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-500">
                        {getStatusText(latestBook.parse_status)}
                      </span>
                      {latestBook.lesson_count !== undefined && latestBook.lesson_count > 0 && (
                        <span className="text-xs text-gray-500">
                          • {latestBook.lesson_count}개 강
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            );
          })()}
        </div>
      ) : (
        <p className="text-gray-400 text-xs text-center py-2">
          등록된 교재가 없습니다.
        </p>
      )}
    </div>
  );
}
