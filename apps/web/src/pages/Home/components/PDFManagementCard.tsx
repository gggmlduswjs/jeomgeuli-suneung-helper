/**
 * PDF 관리 카드
 * 교재 목록 및 업로드
 */
import { useNavigate } from 'react-router-dom';
import { Upload, BookOpen, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import type { Book, ParseStatus } from '../../../types/book';

interface PDFManagementCardProps {
  books: Book[];
  onBookSelect?: (book: Book) => void;
  onSpeak?: (text: string) => void;
}

export default function PDFManagementCard({
  books,
  onBookSelect,
  onSpeak,
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
    <div className="bg-white rounded-lg shadow-md p-6 border-2 border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">교재 관리</h3>
        <button
          onClick={handleUploadClick}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Upload className="w-4 h-4" />
          <span>PDF 업로드</span>
        </button>
      </div>

      {books.length > 0 ? (
        <div className="space-y-3">
          {books.slice(0, 5).map((book) => (
            <button
              key={book.book_id}
              onClick={() => handleBookClick(book)}
              className="w-full flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-left"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                {getStatusIcon(book.parse_status)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">
                    {book.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-500">
                      {getStatusText(book.parse_status)}
                    </span>
                    {book.lesson_count !== undefined && book.lesson_count > 0 && (
                      <span className="text-xs text-gray-500">
                        • {book.lesson_count}개 강
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <p className="text-gray-400 text-sm text-center py-4">
          등록된 교재가 없습니다.
        </p>
      )}
    </div>
  );
}
