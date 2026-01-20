import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import ToastA11y from '../components/system/ToastA11y';
import { examAPI, type Textbook, type Unit } from '../lib/api';
import { curriculumAPI } from '../services/curriculum';
import { useLearnStore } from '../store/learnStore';
import TextbookList from '../components/textbook/TextbookList';
import UnitContent from '../components/textbook/UnitContent';
import PDFUpload from '../components/textbook/PDFUpload';
import { booksAPI } from '../services/books';
import { api } from '../services/api';
import type { Book } from '../types/book';
import { Subject } from '../types/book';

type ViewMode = 'textbooks' | 'units' | 'content';
type ReadingMode = 'braille-only' | 'audio-first' | 'mixed';

export default function Textbook() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  // State
  const [textbooks, setTextbooks] = useState<Textbook[]>([]);
  const [lessons, setLessons] = useState<any[]>([]); // 강의 목록 (lesson.title, lesson.learning_units)
  const [sections, setSections] = useState<any[]>([]); // 현재 선택된 강의의 섹션 목차
  const [units, setUnits] = useState<Unit[]>([]); // 레거시 호환용
  const [currentUnit, setCurrentUnit] = useState<Unit | null>(null);
  const [currentLesson, setCurrentLesson] = useState<any | null>(null); // 현재 선택된 강의
  const [viewMode, setViewMode] = useState<ViewMode>('textbooks');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPDFUpload, setShowPDFUpload] = useState(false);
  
  // URL 파라미터에서 읽기 모드 및 과목 확인
  const readingModeParam = searchParams.get('mode');
  const subjectParam = searchParams.get('subject');
  const readingMode: ReadingMode = readingModeParam === 'braille-read' 
    ? 'braille-only' 
    : readingModeParam === 'audio-first'
    ? 'audio-first'
    : 'mixed'; // 기본값: 혼합 모드 (TTS 활성화)
  
  // 과목 매핑 (korean -> KOREAN 등)
  const subjectMap: Record<string, Subject> = {
    'korean': Subject.KOREAN,
    'english': Subject.ENGLISH,
    'math': Subject.MATH,
  };
  const subject = subjectParam ? (subjectMap[subjectParam.toLowerCase()] || subjectParam.toUpperCase() as Subject) : undefined;
  
  // 디버깅: 과목 변환 확인
  useEffect(() => {
    console.log('[Textbook] URL 파라미터:', { subjectParam, subject, subjectMap });
  }, [subjectParam, subject]);
  
  // Store
  const { currentTextbook, setTextbook, setUnit, setUnits: setStoreUnits } = useLearnStore();

  // 페이지 진입 시 교재 목록 로드 (subject 파라미터 변경 시 재로드)
  useEffect(() => {
    loadTextbooks();
  }, [subjectParam]);

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const subjectName = subjectParam === 'korean' ? '국어' : subjectParam === 'english' ? '영어' : subjectParam === 'math' ? '수학' : '';
    const welcomeMessage = subjectName 
      ? `${subjectName} 교재 목록입니다. 교재를 선택하여 학습할 수 있습니다.`
      : readingMode === 'braille-only'
      ? '수능특강 점자 읽기 모드입니다. 교재를 선택하여 점자로 읽어보세요.'
      : '수능특강 학습 모드입니다. 교재를 선택하여 단원을 학습할 수 있습니다.';
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);
    return () => clearTimeout(timer);
  }, [speak, readingMode, subjectParam]);

  const loadTextbooks = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('[Textbook] 교재 목록 로드 시작:', { subjectParam, subject });
      // booksAPI를 사용하여 과목별 교재 목록 조회
      const data = await booksAPI.list(subject);
      console.log('[Textbook] API 응답:', data);
      // Book 타입을 Textbook 타입으로 변환 (호환성 유지)
      // book_id를 보존하여 커리큘럼 매칭에 사용
      const textbookData = data.map((book, index) => ({
        id: index + 1, // 순차적 숫자 ID (표시용)
        book_id: book.book_id, // 원본 book_id 보존 (커리큘럼 매칭용)
        title: book.title,
        publisher: undefined, // Book 타입에 publisher 필드가 없음
        year: book.year,
        subject: book.subject,
      }));
      console.log('[Textbook] 변환된 교재 데이터:', textbookData);
      setTextbooks(textbookData);
      if (textbookData.length === 0) {
        const subjectName = subjectParam === 'korean' ? '국어' : subjectParam === 'english' ? '영어' : subjectParam === 'math' ? '수학' : '';
        const message = subjectName ? `${subjectName} 교재가 없습니다.` : '등록된 교재가 없습니다.';
        console.warn('[Textbook] 교재가 없습니다:', message);
        speak(message);
      } else {
        console.log(`[Textbook] ${textbookData.length}개의 교재를 불러왔습니다.`);
      }
    } catch (err: any) {
      console.error('[Textbook] 교재 목록 로드 오류:', err);
      const errorMsg = err?.message || '교재 목록을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleTextbookSelect = async (textbook: Textbook) => {
    setTextbook(textbook.id.toString());
    setViewMode('units');
    setLoading(true);
    setError(null);
    
    try {
      // 교재의 커리큘럼 찾기
      // textbook에 book_id가 있으면 사용 (커리큘럼 매칭용)
      const bookId = textbook.book_id;
      
      // book_id가 없으면 subject 기반으로 커리큘럼 생성 시도
      if (!bookId) {
        console.log('[Textbook] book_id가 없음, subject 기반으로 커리큘럼 생성 시도...', { subject: subjectParam });
        try {
          // subject를 pipeline 형식으로 변환 (korean -> literature)
          const pipelineSubject = subjectParam === 'korean' ? 'literature' : subjectParam || 'literature';
          const result = await api.post<{ ok: boolean; curriculum_id?: string; message?: string }>(
            `/curriculum/create-from-pipeline?subject=${encodeURIComponent(pipelineSubject)}&title=${encodeURIComponent(textbook.title || '교재')}`
          );
          
          if (result.ok && result.curriculum_id) {
            console.log('[Textbook] 커리큘럼 생성 성공:', result.curriculum_id);
            // 커리큘럼 생성 후 다시 조회 (book_id 없이 subject로만)
            // subject를 Subject enum으로 변환 (korean -> KOREAN)
            const subjectEnum = subjectParam === 'korean' ? 'KOREAN' : subjectParam?.toUpperCase() || 'KOREAN';
            const newCurricula = await curriculumAPI.list(subjectEnum as any);
            if (newCurricula.length > 0) {
              const curriculum = newCurricula[0];
              const curriculumDetail = await curriculumAPI.get(curriculum.curriculum_id);
              
              // 강의(lesson) 목록만 저장
              setLessons(curriculumDetail.lessons || []);
              
              // 레거시 호환을 위한 unitList도 생성
              const unitList: Unit[] = [];
              let globalOrder = 1;
              for (const lesson of curriculumDetail.lessons || []) {
                for (const learningUnit of lesson.learning_units || []) {
                  const unitIndex = learningUnit.unit_index || 0;
                  const content = learningUnit.content || '';
                  const title = learningUnit.title || learningUnit.section_name || '';
                  
                  unitList.push({
                    id: globalOrder,
                    title: title.trim(),
                    order: lesson.lesson_number * 10000 + unitIndex,
                    content: content,
                    textbook_id: textbook.id,
                  });
                  globalOrder++;
                }
              }
              setUnits(unitList);
              setStoreUnits(unitList);
              
              if (curriculumDetail.lessons?.length === 0) {
                speak(`${textbook.title}에 등록된 강의가 없습니다.`);
              } else {
                speak(`${textbook.title}에 ${curriculumDetail.lessons?.length || 0}개의 강의가 있습니다.`);
              }
              setLoading(false);
              return;
            }
          } else {
            console.error('[Textbook] 커리큘럼 생성 실패:', result);
          }
        } catch (createErr: any) {
          console.error('[Textbook] 커리큘럼 생성 중 오류:', createErr);
        }
        const errorMsg = '교재 ID를 찾을 수 없고, 커리큘럼 생성에도 실패했습니다.';
        setError(errorMsg);
        speak(errorMsg);
        setLoading(false);
        return;
      }
      
      // 교재의 커리큘럼 찾기 (백엔드에서 book_id 필터 지원)
      const curricula = await curriculumAPI.list(undefined, bookId);
      
      if (curricula.length === 0) {
        // 커리큘럼이 없으면 기존 데이터로부터 생성 시도
        console.log('[Textbook] 커리큘럼 없음, 기존 데이터로부터 생성 시도...', { bookId });
        try {
          const result = await api.post<{ ok: boolean; curriculum_id?: string; message?: string }>(
            `/books/${encodeURIComponent(bookId)}/create-curriculum-from-data`
          );
          
          if (result.ok && result.curriculum_id) {
            console.log('[Textbook] 커리큘럼 생성 성공:', result.curriculum_id);
            // 커리큘럼 생성 후 다시 조회
            const newCurricula = await curriculumAPI.list(undefined, bookId);
            if (newCurricula.length > 0) {
              const curriculum = newCurricula[0];
              const curriculumDetail = await curriculumAPI.get(curriculum.curriculum_id);
              
              // 강의(lesson) 목록만 저장 (단원 목록에 강의 제목만 표시)
              setLessons(curriculumDetail.lessons || []);
              
              // 레거시 호환을 위한 unitList도 생성 (섹션 단위)
              const unitList: Unit[] = [];
              let globalOrder = 1;
              for (const lesson of curriculumDetail.lessons || []) {
                for (const learningUnit of lesson.learning_units || []) {
                  const unitIndex = learningUnit.unit_index || 0;
                  const content = learningUnit.content || '';
                  const title = learningUnit.title || learningUnit.section_name || '';
                  
                  unitList.push({
                    id: globalOrder,
                    title: title.trim(),
                    order: lesson.lesson_number * 10000 + unitIndex,
                    content: content,
                    textbook_id: textbook.id,
                  });
                  globalOrder++;
                }
              }
              setUnits(unitList);
              setStoreUnits(unitList);
              
              if (curriculumDetail.lessons?.length === 0) {
                speak(`${textbook.title}에 등록된 강의가 없습니다.`);
              } else {
                speak(`${textbook.title}에 ${curriculumDetail.lessons?.length || 0}개의 강의가 있습니다.`);
              }
              setLoading(false);
              return;
            }
          } else {
            console.error('[Textbook] 커리큘럼 생성 실패:', result);
          }
        } catch (createErr: any) {
          console.error('[Textbook] 커리큘럼 생성 중 오류:', createErr);
          // 404 오류인 경우 백엔드 서버가 실행되지 않았을 수 있음
          if (createErr?.message?.includes('404') || createErr?.message?.includes('Not Found')) {
            console.warn('[Textbook] 백엔드 서버가 실행되지 않았거나 엔드포인트를 찾을 수 없습니다.');
          }
        }
        
        // 커리큘럼 생성 실패 시 기존 오류 메시지 표시
        const errorMsg = `${textbook.title}에 등록된 커리큘럼이 없습니다. 데이터가 있는 경우 자동 생성이 시도되었지만 실패했습니다.`;
        setError(errorMsg);
        speak(errorMsg);
        setLoading(false);
        return;
      }
      
      // 첫 번째 커리큘럼 사용 (일반적으로 교재당 하나의 커리큘럼)
      const curriculum = curricula[0];
      const curriculumDetail = await curriculumAPI.get(curriculum.curriculum_id);
      
      console.log('[Textbook] 커리큘럼 상세:', {
        curriculum_id: curriculumDetail.curriculum_id,
        lessons_count: curriculumDetail.lessons?.length || 0,
        lessons: curriculumDetail.lessons?.map((l: any) => ({
          lesson_number: l.lesson_number,
          title: l.title,
          learning_units_count: l.learning_units?.length || 0,
          section_types: l.learning_units?.map((u: any) => u.section_type) || [],
        })),
      });
      
      // 강의(lesson) 목록만 저장 (단원 목록에 강의 제목만 표시)
      setLessons(curriculumDetail.lessons || []);
      
      // 레거시 호환을 위한 unitList도 생성 (섹션 단위)
      const unitList: Unit[] = [];
      let globalOrder = 1;
      for (const lesson of curriculumDetail.lessons || []) {
        for (const learningUnit of lesson.learning_units || []) {
          const unitIndex = learningUnit.unit_index || 0;
          const content = learningUnit.content || '';
          const title = learningUnit.title || learningUnit.section_name || '';
          
          unitList.push({
            id: globalOrder,
            title: title.trim(),
            order: lesson.lesson_number * 10000 + unitIndex,
            content: content,
            textbook_id: textbook.id,
          });
          globalOrder++;
        }
      }
      setUnits(unitList);
      setStoreUnits(unitList);
      
      if (curriculumDetail.lessons?.length === 0) {
        speak(`${textbook.title}에 등록된 강의가 없습니다.`);
      } else {
        speak(`${textbook.title}에 ${curriculumDetail.lessons?.length || 0}개의 강의가 있습니다.`);
      }
    } catch (err: any) {
      console.error('[Textbook] 단원 목록 로드 오류:', err);
      const errorMsg = err?.message || '단원 목록을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handlePDFUploadComplete = async (textbookId: number) => {
    setShowPDFUpload(false);
    // 새로 업로드된 교재 선택
    await loadTextbooks();
    const uploadedTextbook = textbooks.find(t => t.id === textbookId);
    if (uploadedTextbook) {
      await handleTextbookSelect(uploadedTextbook);
    }
  };


  // 현재 섹션 인덱스 (LiteratureLearning.tsx 스타일)
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);

  // 강의 선택 핸들러 (단원 목록에서 강의 클릭 시) - 바로 학습 화면으로
  const handleLessonSelect = async (lesson: any) => {
    console.log('[Textbook] 강의 선택:', lesson);
    console.log('[Textbook] 강의 정보:', {
      lesson_number: lesson.lesson_number,
      title: lesson.title,
      learning_units_count: lesson.learning_units?.length || 0,
      learning_units: lesson.learning_units,
    });
    
    // 최신 데이터 가져오기 (커리큘럼 재생성 후 반영)
    try {
      const currentTextbookId = textbooks.find(t => t.id.toString() === currentTextbook)?.book_id;
      if (currentTextbookId) {
        const curricula = await curriculumAPI.list(undefined, currentTextbookId);
        if (curricula.length > 0) {
          const curriculumDetail = await curriculumAPI.get(curricula[0].curriculum_id);
          // 최신 강의 데이터로 업데이트
          const updatedLesson = curriculumDetail.lessons?.find(
            (l: any) => l.lesson_number === lesson.lesson_number
          );
          if (updatedLesson) {
            lesson = updatedLesson;
            console.log('[Textbook] 최신 강의 데이터로 업데이트:', {
              lesson_number: lesson.lesson_number,
              learning_units_count: lesson.learning_units?.length || 0,
            });
          }
        }
      }
    } catch (err) {
      console.warn('[Textbook] 최신 데이터 가져오기 실패, 기존 데이터 사용:', err);
    }
    
    setCurrentLesson(lesson);
    let lessonSections = lesson.learning_units || [];
    
    // 1강의 경우 마지막에 핵심 키워드 점자 출력 섹션 추가
    // AI 자동 설명이 각 섹션에서 생성되므로, 키워드 섹션은 나중에 AI 설명을 모아서 생성
    if (lesson.lesson_number === 1) {
      // 키워드 섹션 추가 (AI 설명은 UnitContent에서 생성됨)
      const keywordSection = {
        unit_index: lessonSections.length,
        section_type: 'keywords',
        section_name: '핵심 키워드 정리',
        title: '핵심 키워드 정리',
        content: '', // AI 설명에서 키워드를 추출하므로 초기값은 빈 문자열
        image_path: null,
        problem_metadata: null,
      };
      lessonSections = [...lessonSections, keywordSection];
      console.log('[Textbook] 1강 핵심 키워드 섹션 추가 (AI 설명 기반으로 키워드 추출 예정)');
    }
    
    console.log('[Textbook] 학습 단위 상세:', {
      count: lessonSections.length,
      sections: lessonSections.map((s: any) => ({
        unit_index: s.unit_index,
        section_type: s.section_type,
        title: s.title || s.section_name,
        content_length: s.content?.length || 0,
        has_content: !!s.content,
      })),
    });
    setSections(lessonSections);
    setCurrentSectionIndex(0); // 첫 번째 섹션부터 시작
    setViewMode('content'); // 바로 학습 화면으로
    
    // 이전 데이터 초기화
    setCurrentUnit(null);
    setCurrentSectionIndex(0);
    
    if (lessonSections.length > 0) {
      // 첫 번째 섹션을 현재 단원으로 설정
      const firstSection = lessonSections[0];
      console.log('[Textbook] 첫 번째 섹션:', firstSection);
      const unit: Unit = {
        id: 'section_0', // 고정된 ID 사용 (인덱스 기반)
        title: firstSection.title || firstSection.section_name || '',
        order: firstSection.unit_index || 0,
        content: firstSection.content || '',
        textbook_id: currentTextbook ? parseInt(currentTextbook) : 0,
        image_path: firstSection.image_path,
        problem_metadata: (firstSection as any).problem_metadata || null, // 문제 메타데이터
      };
      // 이전 데이터 제거 후 새 단원 설정
      setTimeout(() => {
        setCurrentUnit(unit);
        setCurrentSectionIndex(0);
        console.log('[Textbook] 현재 단원 설정:', { id: unit.id, title: unit.title, index: 0 });
        speak(`${lesson.title} 학습을 시작합니다.`);
      }, 0);
    } else {
      console.warn('[Textbook] 학습 단위가 없습니다.');
      speak(`${lesson.title}에 학습 단위가 없습니다.`);
    }
  };

  // 섹션 선택 핸들러 (인덱스로)
  const handleSectionSelectByIndex = (index: number) => {
    if (index >= 0 && index < sections.length) {
      const section = sections[index];
      console.log('[Textbook] 섹션 선택:', { index, section, content: section.content });
      
      // 섹션 변경 시 이전 데이터 제거를 위해 새 단원 객체 생성
      const unit: Unit = {
        id: `section_${index}`, // 고정된 ID 사용 (인덱스 기반)
        title: section.title || section.section_name || '',
        order: section.unit_index || index,
        content: section.content || '', // 본문 내용
        textbook_id: currentTextbook ? parseInt(currentTextbook) : 0,
        image_path: section.image_path,
        problem_metadata: (section as any).problem_metadata || null, // 문제 메타데이터
      };
      
      // 섹션 인덱스 먼저 변경 (UnitContent의 key 변경을 트리거)
      setCurrentSectionIndex(index);
      // 그 다음 단원 설정 (key가 변경되므로 이전 컴포넌트는 언마운트됨)
      setCurrentUnit(unit);
      console.log('[Textbook] 현재 단원 설정:', { id: unit.id, title: unit.title, index });
      // speak 호출 제거 - useUnitAudio와 useUnitAIExplanation에서 자동으로 처리
    }
  };

  // 다음 섹션으로 이동
  const handleNextSection = () => {
    const nextIndex = currentSectionIndex + 1;
    console.log('[Textbook] 다음 섹션 클릭:', { 
      currentIndex: currentSectionIndex, 
      nextIndex, 
      sectionsLength: sections.length 
    });
    if (nextIndex < sections.length) {
      handleSectionSelectByIndex(nextIndex);
    } else {
      console.log('[Textbook] 마지막 섹션입니다.');
      speak('마지막 섹션입니다.');
    }
  };

  // 이전 섹션으로 이동
  const handlePrevSection = () => {
    const prevIndex = currentSectionIndex - 1;
    console.log('[Textbook] 이전 섹션 클릭:', { 
      currentIndex: currentSectionIndex, 
      prevIndex 
    });
    if (prevIndex >= 0) {
      handleSectionSelectByIndex(prevIndex);
    } else {
      console.log('[Textbook] 첫 번째 섹션입니다.');
      speak('첫 번째 섹션입니다.');
    }
  };

  // 레거시 호환용
  const handleUnitSelect = async (unit: Unit) => {
    setUnit(unit.id.toString());
    setViewMode('content');
    setLoading(true);
    setError(null);
    
    try {
      const unitData = await examAPI.getUnit(unit.id);
      if (unitData) {
        setCurrentUnit(unitData);
      } else {
        // API에서 가져오지 못하면 직접 설정
        setCurrentUnit(unit);
      }
    } catch (err) {
      // API 실패 시 직접 설정
      setCurrentUnit(unit);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (viewMode === 'content' && currentLesson) {
      // 학습 화면 -> 강의 목록
      setViewMode('units');
      setCurrentLesson(null);
      setSections([]);
      setCurrentUnit(null);
      setCurrentSectionIndex(0);
      speak('강의 목록으로 돌아갑니다.');
    } else if (viewMode === 'units') {
      // 강의 목록 -> 교재 목록
      setViewMode('textbooks');
      setLessons([]);
      setUnits([]);
      speak('교재 목록으로 돌아갑니다.');
    } else {
      navigate('/');
    }
  };

  const handleNextUnit = () => {
    if (viewMode === 'units' && lessons.length > 0) {
      const currentIndex = lessons.findIndex(l => l.lesson_number === currentLesson?.lesson_number);
      if (currentIndex >= 0 && currentIndex < lessons.length - 1) {
        handleLessonSelect(lessons[currentIndex + 1]);
      } else {
        speak('마지막 강의입니다.');
      }
    } else if (viewMode === 'sections' && sections.length > 0) {
      const currentIndex = sections.findIndex(s => 
        (s.title || s.section_name) === currentUnit?.title
      );
      if (currentIndex >= 0 && currentIndex < sections.length - 1) {
        handleSectionSelect(sections[currentIndex + 1]);
      } else {
        speak('마지막 섹션입니다.');
      }
    }
  };

  const handlePrevUnit = () => {
    if (viewMode === 'units' && lessons.length > 0) {
      const currentIndex = lessons.findIndex(l => l.lesson_number === currentLesson?.lesson_number);
      if (currentIndex > 0) {
        handleLessonSelect(lessons[currentIndex - 1]);
      } else {
        speak('첫 번째 강의입니다.');
      }
    } else if (viewMode === 'sections' && sections.length > 0) {
      const currentIndex = sections.findIndex(s => 
        (s.title || s.section_name) === currentUnit?.title
      );
      if (currentIndex > 0) {
        handleSectionSelect(sections[currentIndex - 1]);
      } else {
        speak('첫 번째 섹션입니다.');
      }
    }
  };

  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stopTTS();
      navigate('/');
      stopSTT();
    },
    back: handleBack,
    next: () => {
      // 다음 섹션으로 이동
      if (viewMode === 'content' && sections.length > 0) {
        stopTTS();
        handleNextSection();
        stopSTT();
      } else {
        handleNextUnit();
      }
    },
    prev: () => {
      // 이전 섹션으로 이동
      if (viewMode === 'content' && sections.length > 0) {
        stopTTS();
        handlePrevSection();
        stopSTT();
      } else {
        handlePrevUnit();
      }
    },
    repeat: () => {
      // 현재 섹션의 AI 설명 다시 읽기
      if (viewMode === 'content' && currentUnit) {
        stopTTS();
        // AI 설명이 있으면 다시 읽기
        if (currentUnit.content) {
          speak(currentUnit.content);
        }
      }
    },
    help: () => {
      stopTTS();
      const helpText = '수능특강 학습 모드입니다. 교재를 선택하고 단원을 선택하여 학습할 수 있습니다. 음성으로 "다음", "이전", "반복" 명령을 사용할 수 있습니다.';
      speak(helpText);
    },
  });

  useEffect(() => {
    if (!transcript) return;
    
    const normalized = transcript.toLowerCase().trim();
    
    // 음성 명령 처리
    if (normalized.includes('다음 단원') || normalized.includes('다음단원') || 
        normalized.includes('다음 강의') || normalized.includes('다음강의') ||
        normalized.includes('다음 섹션') || normalized.includes('다음섹션')) {
      stopTTS();
      handleNextUnit();
      stopSTT();
      return;
    }
    
    if (normalized.includes('이전 단원') || normalized.includes('이전단원') ||
        normalized.includes('이전 강의') || normalized.includes('이전강의') ||
        normalized.includes('이전 섹션') || normalized.includes('이전섹션')) {
      stopTTS();
      handlePrevUnit();
      stopSTT();
      return;
    }
    
    if (normalized.includes('첫 번째 교재') || normalized.includes('첫번째 교재')) {
      stopTTS();
      if (textbooks.length > 0) {
        handleTextbookSelect(textbooks[0]);
      }
      stopSTT();
      return;
    }
    
    // 숫자로 교재/강의/섹션 선택
    const numberMatch = normalized.match(/(\d+)\s*(번|번째|번 교재|번 강의|번 섹션|번 단원)/);
    if (numberMatch) {
      const num = parseInt(numberMatch[1]);
      stopTTS();
      if (viewMode === 'textbooks' && num > 0 && num <= textbooks.length) {
        handleTextbookSelect(textbooks[num - 1]);
      } else if (viewMode === 'units' && num > 0 && num <= lessons.length) {
        handleLessonSelect(lessons[num - 1]);
      } else if (viewMode === 'sections' && num > 0 && num <= sections.length) {
        handleSectionSelect(sections[num - 1]);
      }
      stopSTT();
      return;
    }
    
    onSpeech(transcript);
  }, [transcript, onSpeech]);

  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  return (
    <AppShellMobile title="수능특강 학습" className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
        {loading && (
          <div className="text-center py-8">
            <p className="text-muted">로딩 중...</p>
          </div>
        )}

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-4 mb-4">
            <p className="text-error">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <>
            {viewMode === 'textbooks' && (
              <div className="space-y-4">
                {showPDFUpload ? (
                  <div className="space-y-4">
                    <PDFUpload
                      onUploadComplete={handlePDFUploadComplete}
                      onSpeak={speak}
                    />
                    <button
                      onClick={() => {
                        setShowPDFUpload(false);
                      }}
                      className="btn-ghost w-full"
                      aria-label="취소"
                    >
                      취소
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="flex justify-between items-center mb-4">
                      <h2 className="text-lg font-semibold">교재 목록</h2>
                      <button
                        onClick={() => {
                          setShowPDFUpload(true);
                        }}
                        className="btn-primary text-sm"
                        aria-label="PDF 업로드"
                      >
                        PDF 업로드
                      </button>
                    </div>
                    <TextbookList
                      textbooks={textbooks}
                      selectedId={currentTextbook ? parseInt(currentTextbook) : null}
                      onSelect={handleTextbookSelect}
                      onSpeak={speak}
                    />
                  </>
                )}
              </div>
            )}

            {viewMode === 'units' && (
              <div className="space-y-4">
                <button
                  onClick={handleBack}
                  className="btn-ghost mb-4"
                  aria-label="교재 목록으로 돌아가기"
                >
                  ← 교재 목록
                </button>
                <div className="space-y-2">
                  <h2 className="text-lg font-semibold mb-4">강의 목록</h2>
                  {lessons.map((lesson, index) => (
                    <button
                      key={lesson.lesson_number}
                      onClick={() => handleLessonSelect(lesson)}
                      className="w-full p-4 text-left rounded-lg border-2 border-border hover:border-primary/50 transition-colors"
                      aria-label={`${index + 1}번 강의: ${lesson.title}`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">{lesson.title}</div>
                          <div className="text-sm text-muted">
                            {lesson.learning_units?.length || 0}개 섹션
                          </div>
                        </div>
                        <div className="text-sm text-muted">#{index + 1}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {viewMode === 'content' && currentLesson && (
              <div className="space-y-4">
                {/* 헤더 */}
                <div className="bg-white border-b border-gray-200 px-4 py-3 sticky top-0 z-10">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex-1">
                      <h1 className="text-lg font-bold">{currentLesson.title}</h1>
                      <button
                        onClick={handleBack}
                        className="text-xs text-gray-500 hover:text-gray-700 mt-1"
                      >
                        ← 강의 목록으로
                      </button>
                    </div>
                    <button
                      onClick={() => navigate('/')}
                      className="text-sm text-gray-600 hover:text-gray-900"
                    >
                      닫기
                    </button>
                  </div>
                  {/* 진행도 */}
                  {sections.length > 0 && (
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                        <span>{currentSectionIndex + 1} / {sections.length}</span>
                        <span>
                          {sections[currentSectionIndex]?.section_type === 'concept' && '개념'}
                          {sections[currentSectionIndex]?.section_type === 'example' && '예시'}
                          {sections[currentSectionIndex]?.section_type === 'problem' && '문제'}
                          {sections[currentSectionIndex]?.section_type === 'general' && '일반'}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{
                            width: `${((currentSectionIndex + 1) / sections.length) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* 콘텐츠 */}
                <div className="px-4 pb-20">
                  {currentUnit ? (
                    <div className="max-w-3xl mx-auto space-y-4">
                      <UnitContent
                        key={`unit-${currentUnit.id}-${currentSectionIndex}`} // 섹션 변경 시 완전히 새로 마운트
                        unit={currentUnit}
                        onSpeak={speak}
                        readingMode={readingMode}
                        sectionType={sections[currentSectionIndex]?.section_type || 'general'}
                        problemMetadata={(sections[currentSectionIndex] as any)?.problem_metadata}
                        onTTSComplete={() => {
                          // AI 설명 TTS 완료 시 다음 섹션으로 자동 이동
                          console.log('[Textbook] AI 설명 TTS 완료 - 다음 섹션으로 이동');
                          handleNextSection();
                        }}
                        allSections={sections} // keywords 섹션 요약 생성을 위해 전체 섹션 전달
                        currentSectionIndex={currentSectionIndex} // 유사 콘텐츠 추천용
                        onSectionSelect={handleSectionSelectByIndex} // 유사 콘텐츠 클릭 시 섹션 이동
                      />
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <p className="text-gray-500">학습 단위를 불러오는 중...</p>
                    </div>
                  )}
                </div>

                {/* 네비게이션 버튼 (하단 고정) - AppShellMobile 하단 네비게이션 위에 표시 */}
                {sections.length > 0 && (
                  <div className="fixed bottom-16 left-0 right-0 bg-white/95 backdrop-blur-sm border-t border-gray-200 px-4 py-3 z-40 shadow-lg">
                    <div className="flex items-center justify-between max-w-3xl mx-auto">
                      <button
                        onClick={handlePrevSection}
                        disabled={currentSectionIndex === 0}
                        className="px-6 py-2.5 bg-gray-200 text-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300 transition-colors font-medium"
                        aria-label="이전 섹션"
                      >
                        ← 이전
                      </button>
                      <span className="text-sm text-gray-600">
                        {currentSectionIndex + 1} / {sections.length}
                      </span>
                      <button
                        onClick={handleNextSection}
                        disabled={currentSectionIndex >= sections.length - 1}
                        className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                        aria-label="다음 섹션"
                      >
                        다음 →
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={3000}
        onClose={() => setShowToast(false)}
      />
    </AppShellMobile>
  );
}

