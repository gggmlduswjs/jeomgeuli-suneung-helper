/**
 * PDF 페이지에 bbox 마킹 UI
 * YOLO-style 드래그로 영역 선택 및 레이블 지정
 */
import { useState, useRef, useCallback, useEffect } from 'react';
import { X, Save } from 'lucide-react';
import type { ParsingGuideRegion } from '../../services/templates';
import * as pdfjsLib from 'pdfjs-dist';

// PDF.js worker 설정
if (typeof window !== 'undefined') {
  // 로컬 worker 파일 사용 (public 폴더에 복사됨)
  pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';
}

interface PDFBboxMarkerProps {
  pdfUrl: string;
  pageNumber: number;
  existingRegions: ParsingGuideRegion[];
  onRegionsChange: (regions: ParsingGuideRegion[]) => void;
  onClose: () => void;
}

interface DrawingBox {
  id: string;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

const UNIT_LABELS = [
  { value: 'concept', label: '개념', color: 'bg-blue-500/30 border-blue-500' },
  { value: 'passage', label: '본문', color: 'bg-green-500/30 border-green-500' },
  { value: 'problem', label: '문제', color: 'bg-purple-500/30 border-purple-500' },
];

export default function PDFBboxMarker({
  pdfUrl,
  pageNumber,
  existingRegions,
  onRegionsChange,
  onClose,
}: PDFBboxMarkerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPos, setStartPos] = useState<{ x: number; y: number } | null>(null);
  const [currentBox, setCurrentBox] = useState<DrawingBox | null>(null);
  const [boxes, setBoxes] = useState<DrawingBox[]>([]);
  const [selectedLabel, setSelectedLabel] = useState<string>('concept');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfRendered, setPdfRendered] = useState(false);
  const [pdfRenderTask, setPdfRenderTask] = useState<(() => Promise<void>) | null>(null);
  const renderTaskRef = useRef<any>(null); // 현재 렌더링 작업 추적
  const pdfImageDataRef = useRef<ImageData | null>(null); // 렌더링된 PDF 이미지 데이터 저장

  // 기존 regions를 boxes로 변환
  useEffect(() => {
    const pageRegions = existingRegions.filter(r => r.page === pageNumber);
    const convertedBoxes: DrawingBox[] = pageRegions.map((region, idx) => {
      const [x_min, y_min, x_max, y_max] = region.bbox;
      return {
        id: `existing-${idx}`,
        label: region.label,
        x: x_min,
        y: y_min,
        width: x_max - x_min,
        height: y_max - y_min,
      };
    });
    setBoxes(convertedBoxes);
  }, [existingRegions, pageNumber]);

  // PDF 페이지 렌더링
  useEffect(() => {
    const loadPdfPage = async () => {
      if (!pdfUrl) return;
      
      setLoading(true);
      setError(null);
      
      try {
        // PDF.js로 PDF 로드 (폰트 렌더링 활성화)
        const loadingTask = pdfjsLib.getDocument({ 
          url: pdfUrl,
          // 표준 폰트 데이터 URL (로컬 파일 사용)
          standardFontDataUrl: '/standard_fonts/',
          // CMap URL (한글 폰트 렌더링용)
          cMapUrl: `https://unpkg.com/pdfjs-dist@${pdfjsLib.version}/cmaps/`,
          cMapPacked: true,
          // 폰트 렌더링 활성화
          disableFontFace: false,
          // 시스템 폰트 사용 비활성화 (표준 폰트 사용)
          useSystemFonts: false,
        });
        const pdf = await loadingTask.promise;
        
        // 총 페이지 수 확인
        const totalPages = pdf.numPages;
        if (pageNumber < 1 || pageNumber > totalPages) {
          setError(`페이지 번호가 범위를 벗어났습니다. (1-${totalPages})`);
          setLoading(false);
          return;
        }
        
        // 지정된 페이지 가져오기
        const page = await pdf.getPage(pageNumber);
        
        // 캔버스 설정
        if (!canvasRef.current || !containerRef.current) {
          setLoading(false);
          return;
        }
        
        const canvas = canvasRef.current;
        const container = containerRef.current;
        const containerWidth = container.clientWidth || 800;
        
        // 초기 뷰포트 (고해상도)
        const initialViewport = page.getViewport({ scale: 2.0 });
        
        // 컨테이너에 맞게 스케일 조정
        const displayScale = containerWidth / initialViewport.width;
        const scaledViewport = page.getViewport({ scale: displayScale * 2.0 });
        
        canvas.width = scaledViewport.width;
        canvas.height = scaledViewport.height;

        // 이전 렌더링 작업 취소
        if (renderTaskRef.current) {
          renderTaskRef.current.cancel();
        }

        // PDF 페이지를 캔버스에 렌더링
        const ctx = canvas.getContext('2d')!;
        const renderContext = {
          canvasContext: ctx,
          viewport: scaledViewport,
          canvas: canvas
        };
        const renderTask = page.render(renderContext);
        renderTaskRef.current = renderTask;
        await renderTask.promise;

        // 렌더링된 PDF 이미지 데이터 저장 (bbox 그릴 때 재사용)
        pdfImageDataRef.current = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        // 텍스트 레이어 렌더링 (선택적, 폰트가 제대로 로드되지 않을 경우)
        try {
          const textContent = await page.getTextContent();
          // 텍스트가 제대로 로드되었는지 확인
          if (textContent.items.length === 0) {
            console.warn('PDF 텍스트 콘텐츠를 찾을 수 없습니다.');
          }
        } catch (textError) {
          console.warn('텍스트 레이어 로드 실패:', textError);
        }
        
        // PDF 재렌더링 함수 저장 (bbox 그릴 때 사용 - 저장된 이미지 데이터 복원)
        const renderPdf = async () => {
          // 저장된 PDF 이미지 데이터를 복원 (재렌더링 없이)
          if (pdfImageDataRef.current && canvasRef.current) {
            const ctx = canvasRef.current.getContext('2d');
            if (ctx) {
              ctx.putImageData(pdfImageDataRef.current, 0, 0);
            }
          }
        };
        setPdfRenderTask(() => renderPdf);
        setPdfRendered(true);
        
        setLoading(false);
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : 'PDF를 불러올 수 없습니다.';
        console.error('PDF 로드 실패:', message);
        setError(message);
        setLoading(false);
        setPdfRendered(false);
      }
    };
    
    setPdfRendered(false);
    // 이전 렌더링 작업 취소
    if (renderTaskRef.current) {
      renderTaskRef.current.cancel();
      renderTaskRef.current = null;
    }
    loadPdfPage();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pdfUrl, pageNumber]);
  
  // 컴포넌트 언마운트 시 렌더링 작업 취소
  useEffect(() => {
    return () => {
      if (renderTaskRef.current) {
        renderTaskRef.current.cancel();
      }
    };
  }, []);

  // 마우스 이벤트 핸들러
  const getMousePos = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return { x: 0, y: 0 };
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    return { x, y };
  }, []);

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const pos = getMousePos(e);
    setIsDrawing(true);
    setStartPos(pos);
    setCurrentBox({
      id: `temp-${Date.now()}`,
      label: selectedLabel,
      x: pos.x,
      y: pos.y,
      width: 0,
      height: 0,
    });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !startPos || !currentBox) return;
    
    const pos = getMousePos(e);
    const width = pos.x - startPos.x;
    const height = pos.y - startPos.y;
    
    setCurrentBox({
      ...currentBox,
      width,
      height,
    });
    
    // 캔버스 다시 그리기 (requestAnimationFrame으로 최적화)
    requestAnimationFrame(() => {
      drawCanvas().catch(() => {
        // RenderingCancelledException은 무시 (정상적인 동작)
      });
    });
  };

  const handleMouseUp = () => {
    if (!isDrawing || !currentBox) return;
    
    // 최소 크기 체크
    if (Math.abs(currentBox.width) > 10 && Math.abs(currentBox.height) > 10) {
      const normalizedBox: DrawingBox = {
        ...currentBox,
        x: currentBox.width < 0 ? currentBox.x + currentBox.width : currentBox.x,
        y: currentBox.height < 0 ? currentBox.y + currentBox.height : currentBox.y,
        width: Math.abs(currentBox.width),
        height: Math.abs(currentBox.height),
      };
      
      setBoxes(prev => [...prev, normalizedBox]);
    }
    
    setIsDrawing(false);
    setStartPos(null);
    setCurrentBox(null);
    drawCanvas().catch(console.error);
  };

  // 캔버스 그리기 (PDF 이미지 복원 + bbox 그리기)
  const drawCanvas = useCallback(async () => {
    if (!canvasRef.current || !pdfRendered || !pdfRenderTask) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // PDF 이미지 데이터 복원 (재렌더링 없이)
    await pdfRenderTask();
    
    // 그 다음 bbox 그리기
    // 기존 박스 그리기
    boxes.forEach(box => {
      const labelConfig = UNIT_LABELS.find(l => l.value === box.label) || UNIT_LABELS[0];
      
      // 색상 추출
      let strokeColor = '#3b82f6'; // 기본 파란색
      if (box.label === 'concept') strokeColor = '#3b82f6'; // 파란색
      else if (box.label === 'passage') strokeColor = '#10b981'; // 초록색
      else if (box.label === 'problem') strokeColor = '#a855f7'; // 보라색
      
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 3;
      ctx.strokeRect(
        box.x,
        box.y,
        box.width,
        box.height
      );
      
      // 레이블 배경
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      const labelWidth = labelConfig.label.length * 10 + 10;
      ctx.fillRect(
        box.x,
        Math.max(0, box.y - 20),
        labelWidth,
        20
      );
      
      // 레이블 텍스트
      ctx.fillStyle = 'white';
      ctx.font = '12px sans-serif';
      ctx.fillText(
        labelConfig.label,
        box.x + 5,
        Math.max(15, box.y - 5)
      );
    });
    
    // 현재 그리는 박스 그리기
    if (currentBox) {
      let strokeColor = '#3b82f6';
      if (currentBox.label === 'concept') strokeColor = '#3b82f6';
      else if (currentBox.label === 'passage') strokeColor = '#10b981';
      else if (currentBox.label === 'problem') strokeColor = '#a855f7';
      
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 3;
      ctx.setLineDash([5, 5]);
      ctx.strokeRect(
        currentBox.x,
        currentBox.y,
        currentBox.width,
        currentBox.height
      );
      ctx.setLineDash([]);
    }
  }, [boxes, currentBox, pdfRendered, pdfRenderTask]);

  // PDF 렌더링 후 및 boxes 변경 시 bbox 그리기
  useEffect(() => {
    if (pdfRendered && pdfRenderTask) {
      // 약간의 지연을 두어 PDF 렌더링이 완전히 완료되도록 함
      const timer = setTimeout(() => {
        drawCanvas().catch(console.error);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [pdfRendered, pdfRenderTask, boxes, currentBox, drawCanvas]);

  // 박스 삭제
  const handleDeleteBox = (id: string) => {
    setBoxes(prev => prev.filter(b => b.id !== id));
    setTimeout(() => drawCanvas().catch(console.error), 0);
  };

  // 저장
  const handleSave = () => {
    const regions: ParsingGuideRegion[] = boxes.map(box => ({
      page: pageNumber,
      label: box.label,
      bbox: [
        box.x,
        box.y,
        box.x + box.width,
        box.y + box.height,
      ] as [number, number, number, number],
    }));
    
    // 다른 페이지의 regions 유지
    const otherRegions = existingRegions.filter(r => r.page !== pageNumber);
    onRegionsChange([...otherRegions, ...regions]);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-background rounded-lg shadow-xl w-full max-w-6xl h-[90vh] flex flex-col">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h2 className="text-lg font-semibold">페이지 {pageNumber} 영역 마킹</h2>
            <p className="text-sm text-muted-foreground">
              드래그로 영역을 선택하고 레이블을 지정하세요
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-secondary rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 레이블 선택 */}
        <div className="p-4 border-b flex items-center gap-2">
          <span className="text-sm font-medium">레이블:</span>
          {UNIT_LABELS.map(label => (
            <button
              key={label.value}
              onClick={() => setSelectedLabel(label.value)}
              className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                selectedLabel === label.value
                  ? label.color + ' border-2'
                  : 'bg-secondary hover:bg-secondary/80'
              }`}
            >
              {label.label}
            </button>
          ))}
          <div className="flex-1" />
          <span className="text-sm text-muted-foreground">
            {boxes.length}개 영역 마킹됨
          </span>
        </div>

        {/* PDF 뷰어 */}
        <div ref={containerRef} className="flex-1 overflow-auto p-4 bg-gray-100">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-sm text-muted-foreground">PDF 로딩 중...</p>
              </div>
            </div>
          )}
          {error && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-error text-sm">{error}</p>
              </div>
            </div>
          )}
          {!loading && !error && (
            <canvas
              ref={canvasRef}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              className="cursor-crosshair border border-border"
              style={{ maxWidth: '100%', height: 'auto', display: 'block' }}
            />
          )}
        </div>

        {/* 마킹된 영역 목록 */}
        {boxes.length > 0 && (
          <div className="p-4 border-t max-h-32 overflow-y-auto">
            <div className="text-sm font-medium mb-2">마킹된 영역:</div>
            <div className="flex flex-wrap gap-2">
              {boxes.map((box) => {
                const labelConfig = UNIT_LABELS.find(l => l.value === box.label) || UNIT_LABELS[0];
                return (
                  <div
                    key={box.id}
                    className={`px-3 py-1 rounded-lg text-xs flex items-center gap-2 ${labelConfig.color}`}
                  >
                    <span>{labelConfig.label}</span>
                    <span className="text-muted-foreground">
                      ({Math.round(box.x)}, {Math.round(box.y)}, {Math.round(box.width)}, {Math.round(box.height)})
                    </span>
                    <button
                      onClick={() => handleDeleteBox(box.id)}
                      className="ml-1 hover:text-danger"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 푸터 */}
        <div className="p-4 border-t flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
          >
            취소
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            저장
          </button>
        </div>
      </div>
    </div>
  );
}
