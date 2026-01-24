/**
 * Unit 페이지 네비게이션 관리 훅
 */
import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Unit } from '../types/unit';
import { ROUTES } from '../constants';

export interface UseUnitNavigationReturn {
  handlePrevUnit: (currentUnit: Unit | null, allUnits: Unit[]) => void;
  handleNextUnit: (currentUnit: Unit | null, allUnits: Unit[], onLastUnit?: () => void) => void;
  navigateToUnit: (unitId: string) => void;
}

/**
 * Unit 네비게이션 관리 훅
 */
export function useUnitNavigation(): UseUnitNavigationReturn {
  const navigate = useNavigate();

  const navigateToUnit = useCallback((unitId: string) => {
    navigate(ROUTES.UNIT(unitId));
  }, [navigate]);

  const handlePrevUnit = useCallback((currentUnit: Unit | null, allUnits: Unit[]) => {
    if (!currentUnit) return;
    
    const currentIndex = allUnits.findIndex(u => u.unit_id === currentUnit.unit_id);
    if (currentIndex > 0) {
      const prevUnit = allUnits[currentIndex - 1];
      navigateToUnit(prevUnit.unit_id);
    }
  }, [navigateToUnit]);

  const handleNextUnit = useCallback((
    currentUnit: Unit | null, 
    allUnits: Unit[],
    onLastUnit?: () => void
  ) => {
    if (!currentUnit) return;
    
    const currentIndex = allUnits.findIndex(u => u.unit_id === currentUnit.unit_id);
    if (currentIndex < allUnits.length - 1) {
      const nextUnit = allUnits[currentIndex + 1];
      navigateToUnit(nextUnit.unit_id);
    } else if (onLastUnit) {
      onLastUnit();
    }
  }, [navigateToUnit]);

  return {
    handlePrevUnit,
    handleNextUnit,
    navigateToUnit,
  };
}

export default useUnitNavigation;
