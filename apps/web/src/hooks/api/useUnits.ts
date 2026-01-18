/**
 * 학습 단위 관련 훅
 */
import { useState, useCallback } from 'react';
import { unitsAPI } from '../../services/units';
import type { Unit } from '../../types/unit';

export function useUnits(lessonId?: string) {
  const [units, setUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadUnits = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await unitsAPI.list(id);
      setUnits(data);
      return data;
    } catch (err: any) {
      setError(err.message || '학습 단위 목록을 불러오는 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getUnit = useCallback(async (unitId: string) => {
    setLoading(true);
    setError(null);
    try {
      const unit = await unitsAPI.get(unitId);
      return unit;
    } catch (err: any) {
      setError(err.message || '학습 단위를 불러오는 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    units,
    loading,
    error,
    loadUnits,
    getUnit,
  };
}
