/**
 * /learn/:bookId/:lessonId/:questionId 경로를 /unit/:unitId로 리다이렉트
 * 호환성을 위한 리다이렉트 컴포넌트
 */
import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

export default function LearnRedirect() {
  const navigate = useNavigate();
  const { questionId } = useParams<{ bookId: string; lessonId: string; questionId: string }>();

  useEffect(() => {
    // questionId가 실제로는 unitId이므로 바로 리다이렉트
    if (questionId) {
      navigate(`/unit/${questionId}`, { replace: true });
    } else {
      navigate('/books', { replace: true });
    }
  }, [navigate, questionId]);

  return null;
}
