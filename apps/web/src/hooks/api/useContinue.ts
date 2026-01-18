/**
 * 이어하기 훅
 * 진도 조회 + 자동 이동
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProgress } from './useProgress';

export function useContinue(userId: string = 'u_demo', autoNavigate: boolean = false) {
  const navigate = useNavigate();
  const { progress, loading, getContinue } = useProgress();

  useEffect(() => {
    getContinue(userId);
  }, [userId, getContinue]);

  useEffect(() => {
    if (autoNavigate && progress?.unit_id && !loading) {
      navigate(`/unit/${progress.unit_id}`);
    }
  }, [progress, loading, autoNavigate, navigate]);

  return {
    progress,
    loading,
    navigateToContinue: () => {
      if (progress?.unit_id) {
        navigate(`/unit/${progress.unit_id}`);
      }
    },
  };
}
