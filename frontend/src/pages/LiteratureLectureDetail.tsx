/**
 * 문학 강의 상세 페이지
 * 강의 정보, 개념 설명, 작품 본문을 표시
 */
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import ToastA11y from '../components/system/ToastA11y';
import { usePageBase } from '../hooks/usePageBase';
import { literatureAPI } from '../services/literature';
import { createModuleLogger } from '../utils/logger';
import { useLiteratureProgressStore } from '../store/literatureProgressStore';

const logger = createModuleLogger('LiteratureLectureDetail');

// 강의 상세 타입 확장
interface LectureWork {
  work_id: string;
  title: string;
  author: string;
  genre: string;
  year?: number;
  content: string[];
  themes?: string[];
  analysis?: {
    형식?: string;
    운율?: string;
    이미지?: string;
    표현법?: string;
    주제?: string;
  };
  key_points?: string[];
}

interface LectureConcept {
  concept_id: string;
  title: string;
  content: string[];
}

interface LectureProblem {
  problem_id: string;
  problem_number: number;
  question_text: string;
  passage_required: boolean;
  reference?: string;
  choices: Record<string, string>;
  correct_answer: string;
  explanation: string;
  difficulty: string;
  points: number;
}

interface LectureDetailData {
  lecture_id: number;
  title: string;
  subject: string;
  description: string;
  concepts: LectureConcept[];
  works: LectureWork[];
  problems: LectureProblem[];
  keywords: string[];
  learning_objectives?: string[];
  estimated_time?: number;
  difficulty?: string;
}

export default function LiteratureLectureDetail() {
  const { lectureId } = useParams<{ lectureId: string }>();
  const navigate = useNavigate();
  const [lecture, setLecture] = useState<LectureDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [showAnswers, setShowAnswers] = useState<Record<string, boolean>>({});

  // 진도 관리
  const {
    setLastLecture,
    completeLecture,
    isLectureCompleted,
    saveProblemResult,
    addStudyTime,
  } = useLiteratureProgressStore();

  const [studyStartTime] = useState(Date.now());

  const {
    speak,
    stopTTS,
    stopSTT,
    isListening,
    transcript,
    showToast,
    toastMessage,
    setShowToast,
    showToastMessage,
  } = usePageBase({
    autoAnnounce: lecture ? `${lecture.title}. ${lecture.description}` : '강의를 불러오는 중입니다.',
    voiceCommands: {
      home: () => {
        stopTTS();
        navigate('/');
        showToastMessage('홈으로 이동합니다.');
        speak('홈으로 이동합니다.');
        stopSTT();
      },
      back: () => {
        stopTTS();
        navigate('/literature/lectures');
        showToastMessage('강의 목록으로 돌아갑니다.');
        speak('강의 목록으로 돌아갑니다.');
        stopSTT();
      },
    },
  });

  // 강의 상세 로드
  useEffect(() => {
    if (lectureId) {
      const id = parseInt(lectureId);
      loadLectureDetail(id);
      setLastLecture(id);
    }
  }, [lectureId]);

  // 페이지 나가기 전 학습 시간 저장
  useEffect(() => {
    return () => {
      const studyTime = Math.floor((Date.now() - studyStartTime) / 1000);
      addStudyTime(studyTime);
    };
  }, [studyStartTime]);

  const loadLectureDetail = async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await literatureAPI.getLecture(id) as any;
      setLecture(data);
      logger.log(`강의 ${id} 로드 완료`);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '강의를 불러오지 못했습니다.';
      setError(errorMsg);
      logger.error('강의 로드 실패:', err);
      showToastMessage(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 섹션 토글
  const toggleSection = (sectionId: string) => {
    setExpandedSection(expandedSection === sectionId ? null : sectionId);
  };

  // 텍스트 읽기
  const readText = (text: string | string[]) => {
    const content = Array.isArray(text) ? text.join(' ') : text;
    speak(content);
  };

  // 개념 읽기
  const readConcept = (concept: LectureConcept) => {
    const text = `${concept.title}. ${concept.content.join(' ')}`;
    speak(text);
  };

  // 작품 읽기
  const readWork = (work: LectureWork) => {
    const text = `${work.title}, ${work.author}. ${work.content.join(' ')}`;
    speak(text);
  };

  // 답안 선택
  const handleAnswerSelect = (problemId: string, answer: string) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [problemId]: answer,
    }));
    showToastMessage(`${answer}번 선택`);
  };

  // 정답 확인
  const handleCheckAnswer = (problem: LectureProblem) => {
    const selected = selectedAnswers[problem.problem_id];
    if (!selected) {
      showToastMessage('답을 선택해주세요.');
      speak('답을 선택해주세요.');
      return;
    }

    const isCorrect = selected === problem.correct_answer;
    setShowAnswers((prev) => ({
      ...prev,
      [problem.problem_id]: true,
    }));

    // 문제 결과 저장
    saveProblemResult(problem.problem_id, selected, isCorrect);

    if (isCorrect) {
      showToastMessage('정답입니다!');
      speak(`정답입니다! ${problem.explanation}`);
    } else {
      showToastMessage(`오답입니다. 정답은 ${problem.correct_answer}번입니다.`);
      speak(`오답입니다. 정답은 ${problem.correct_answer}번입니다. ${problem.explanation}`);
    }

    // 모든 문제를 풀었으면 강의 완료 처리
    if (lecture) {
      const allProblemsAnswered = lecture.problems.every(
        (p) => showAnswers[p.problem_id] || p.problem_id === problem.problem_id
      );
      if (allProblemsAnswered && !isLectureCompleted(lecture.lecture_id)) {
        completeLecture(lecture.lecture_id);
        showToastMessage('강의를 완료했습니다!');
        speak('모든 문제를 풀었습니다. 강의를 완료했습니다!');
      }
    }
  };

  // 문제 읽기
  const readProblem = (problem: LectureProblem) => {
    const choicesText = Object.entries(problem.choices)
      .map(([num, text]) => `${num}번. ${text}`)
      .join('. ');
    const text = `문제 ${problem.problem_number}. ${problem.question_text}. 선택지. ${choicesText}`;
    speak(text);
  };;

  if (loading) {
    return (
      <AppShellMobile title="강의 상세" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1">
          <p className="text-muted" role="status" aria-live="polite">
            강의를 불러오는 중...
          </p>
        </div>
      </AppShellMobile>
    );
  }

  if (error || !lecture) {
    return (
      <AppShellMobile title="강의 상세" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1 px-4">
          <div className="bg-destructive/10 border border-destructive rounded-lg p-6 max-w-md">
            <h3 className="text-lg font-semibold text-destructive mb-2">오류 발생</h3>
            <p className="text-sm mb-4">{error || '강의를 찾을 수 없습니다.'}</p>
            <button
              onClick={() => navigate('/literature/lectures')}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              aria-label="강의 목록으로 돌아가기"
            >
              강의 목록으로
            </button>
          </div>
        </div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile title={lecture.title} className="relative h-screen flex flex-col">
      <div className="mb-2">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="px-2 py-1 space-y-3 flex-1 overflow-y-auto min-h-0">
        {/* 강의 헤더 */}
        <div className="bg-card border border-border rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <h2 className="text-xl font-bold">{lecture.title}</h2>
            <button
              onClick={() => readText(lecture.description)}
              className="ml-2 px-3 py-1 text-xs bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors"
              aria-label="강의 소개 읽기"
            >
              읽기
            </button>
          </div>
          <p className="text-sm text-muted mb-3">{lecture.description}</p>

          {/* 메타 정보 */}
          <div className="flex flex-wrap gap-2 text-xs">
            {lecture.estimated_time && (
              <span className="px-2 py-1 bg-secondary/50 text-secondary-foreground rounded">
                ⏱️ {lecture.estimated_time}분
              </span>
            )}
            {lecture.difficulty && (
              <span className="px-2 py-1 bg-secondary/50 text-secondary-foreground rounded">
                📊 난이도: {lecture.difficulty}
              </span>
            )}
            {lecture.keywords && lecture.keywords.map((keyword, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-primary/10 text-primary rounded"
              >
                #{keyword}
              </span>
            ))}
          </div>
        </div>

        {/* 학습 목표 */}
        {lecture.learning_objectives && lecture.learning_objectives.length > 0 && (
          <div className="bg-card border border-border rounded-lg p-4">
            <h3 className="text-lg font-semibold mb-2">📚 학습 목표</h3>
            <ul className="space-y-1 text-sm">
              {lecture.learning_objectives.map((objective, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>{objective}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 개념 설명 */}
        {lecture.concepts && lecture.concepts.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-lg font-semibold px-2">💡 개념 설명</h3>
            {lecture.concepts.map((concept) => (
              <div
                key={concept.concept_id}
                className="bg-card border border-border rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => toggleSection(concept.concept_id)}
                  className="w-full p-4 text-left flex items-center justify-between hover:bg-accent/50 transition-colors"
                  aria-expanded={expandedSection === concept.concept_id}
                  aria-label={`${concept.title} 개념 설명`}
                >
                  <span className="font-semibold">{concept.title}</span>
                  <div className="flex items-center gap-2">
                    <div
                      onClick={(e) => {
                        e.stopPropagation();
                        readConcept(concept);
                      }}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          e.stopPropagation();
                          readConcept(concept);
                        }
                      }}
                      className="px-3 py-1 text-xs bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/50"
                      aria-label={`${concept.title} 읽기`}
                    >
                      읽기
                    </div>
                    <span className="text-xl">
                      {expandedSection === concept.concept_id ? '▼' : '▶'}
                    </span>
                  </div>
                </button>
                {expandedSection === concept.concept_id && (
                  <div className="px-4 pb-4 space-y-2">
                    {concept.content.map((line, idx) => (
                      <p key={idx} className="text-sm">
                        {line}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* 문제 풀이 */}
        {lecture.problems && lecture.problems.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-lg font-semibold px-2">✏️ 문제 풀이</h3>
            {lecture.problems.map((problem) => {
              const selected = selectedAnswers[problem.problem_id];
              const showAnswer = showAnswers[problem.problem_id];
              const isCorrect = selected === problem.correct_answer;

              return (
                <div
                  key={problem.problem_id}
                  className="bg-card border border-border rounded-lg p-4 space-y-3"
                >
                  {/* 문제 헤더 */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-bold text-primary">
                          {problem.problem_number}번
                        </span>
                        <span className="text-xs px-2 py-0.5 bg-secondary/50 rounded">
                          {problem.difficulty}
                        </span>
                        <span className="text-xs px-2 py-0.5 bg-secondary/50 rounded">
                          {problem.points}점
                        </span>
                      </div>
                      <p className="font-medium mb-2">{problem.question_text}</p>
                    </div>
                    <button
                      onClick={() => readProblem(problem)}
                      className="ml-2 px-3 py-1 text-xs bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors"
                      aria-label="문제 읽기"
                    >
                      읽기
                    </button>
                  </div>

                  {/* 보기 (있는 경우) */}
                  {problem.reference && (
                    <div className="bg-muted/30 rounded p-3 text-sm" style={{ whiteSpace: 'pre-wrap' }}>
                      <p className="font-medium mb-1">&lt;보기&gt;</p>
                      {problem.reference}
                    </div>
                  )}

                  {/* 선택지 */}
                  <div className="space-y-2">
                    {Object.entries(problem.choices).map(([num, text]) => {
                      const isSelected = selected === num;
                      const isCorrectChoice = num === problem.correct_answer;

                      return (
                        <button
                          key={num}
                          onClick={() => handleAnswerSelect(problem.problem_id, num)}
                          disabled={showAnswer}
                          className={`w-full text-left p-3 rounded border transition-colors ${
                            showAnswer
                              ? isCorrectChoice
                                ? 'bg-success/10 border-success'
                                : isSelected
                                ? 'bg-destructive/10 border-destructive'
                                : 'bg-muted/30 border-border/50'
                              : isSelected
                              ? 'bg-primary/10 border-primary'
                              : 'bg-muted/10 border-border hover:border-primary/50'
                          }`}
                          aria-label={`${num}번 선택지`}
                          aria-pressed={isSelected}
                        >
                          <div className="flex items-start">
                            <span className="font-semibold min-w-[24px]">{num}.</span>
                            <span className="ml-2">{text}</span>
                            {showAnswer && isCorrectChoice && (
                              <span className="ml-auto text-success font-bold">✓</span>
                            )}
                            {showAnswer && isSelected && !isCorrectChoice && (
                              <span className="ml-auto text-destructive font-bold">✗</span>
                            )}
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  {/* 정답 확인 버튼 */}
                  {!showAnswer && (
                    <button
                      onClick={() => handleCheckAnswer(problem)}
                      className="w-full px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 transition-colors font-semibold"
                      aria-label="정답 확인"
                    >
                      정답 확인
                    </button>
                  )}

                  {/* 해설 */}
                  {showAnswer && (
                    <div className={`p-3 rounded ${
                      isCorrect ? 'bg-success/10' : 'bg-muted/30'
                    }`}>
                      <p className="font-semibold mb-1">
                        {isCorrect ? '✅ 정답입니다!' : `❌ 오답입니다. 정답: ${problem.correct_answer}번`}
                      </p>
                      <p className="text-sm">{problem.explanation}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* 작품 본문 */}
        {lecture.works && lecture.works.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-lg font-semibold px-2">📖 작품</h3>
            {lecture.works.map((work) => (
              <div
                key={work.work_id}
                className="bg-card border border-border rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => toggleSection(work.work_id)}
                  className="w-full p-4 text-left flex items-center justify-between hover:bg-accent/50 transition-colors"
                  aria-expanded={expandedSection === work.work_id}
                  aria-label={`${work.title} 작품 본문`}
                >
                  <div>
                    <span className="font-semibold">{work.title}</span>
                    <span className="text-sm text-muted ml-2">- {work.author}</span>
                    {work.year && (
                      <span className="text-xs text-muted ml-2">({work.year})</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      onClick={(e) => {
                        e.stopPropagation();
                        readWork(work);
                      }}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          e.stopPropagation();
                          readWork(work);
                        }
                      }}
                      className="px-3 py-1 text-xs bg-primary/10 text-primary rounded hover:bg-primary/20 transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/50"
                      aria-label={`${work.title} 읽기`}
                    >
                      읽기
                    </div>
                    <span className="text-xl">
                      {expandedSection === work.work_id ? '▼' : '▶'}
                    </span>
                  </div>
                </button>
                {expandedSection === work.work_id && (
                  <div className="px-4 pb-4 space-y-4">
                    {/* 작품 본문 */}
                    <div className="bg-muted/30 rounded-lg p-3 space-y-1">
                      {work.content.map((line, idx) => (
                        <p key={idx} className="text-sm" style={{ whiteSpace: 'pre-wrap' }}>
                          {line}
                        </p>
                      ))}
                    </div>

                    {/* 작품 분석 */}
                    {work.analysis && (
                      <div className="space-y-2">
                        <h4 className="font-semibold text-sm">📝 작품 분석</h4>
                        <div className="grid grid-cols-1 gap-2 text-sm">
                          {Object.entries(work.analysis).map(([key, value]) => (
                            <div key={key} className="flex">
                              <span className="font-medium min-w-[60px]">{key}:</span>
                              <span className="text-muted">{value}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 핵심 포인트 */}
                    {work.key_points && work.key_points.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-semibold text-sm">✨ 핵심 포인트</h4>
                        <ul className="space-y-1 text-sm">
                          {work.key_points.map((point, idx) => (
                            <li key={idx} className="flex items-start">
                              <span className="mr-2">•</span>
                              <span>{point}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* 주제 */}
                    {work.themes && work.themes.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {work.themes.map((theme, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 text-xs bg-accent/50 text-accent-foreground rounded"
                          >
                            {theme}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 하단 네비게이션 */}
      <div className="border-t border-border p-2 bg-background">
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/literature/lectures')}
            className="flex-1 px-4 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors font-semibold"
            aria-label="강의 목록으로"
          >
            강의 목록
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex-1 px-4 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors font-semibold"
            aria-label="홈으로"
          >
            홈으로
          </button>
        </div>
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
