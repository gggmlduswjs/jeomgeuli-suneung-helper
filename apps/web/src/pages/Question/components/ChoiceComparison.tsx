/**
 * 선택지 비교 모드
 * 보호자용 시각 테이블 + 시각장애인용 음성 안내
 */
import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import useTTS from '../../../hooks/useTTS';

interface Choice {
  number: number;
  text: string;
  coreClaim: string;
  errorType: string;
  evidenceSentence: string;
  isCorrect: boolean;
}

interface ChoiceComparisonProps {
  choices: Choice[];
  questionText: string;
}

export default function ChoiceComparison({
  choices,
  questionText
}: ChoiceComparisonProps) {
  const { speak, stop: stopTTS } = useTTS();
  const [selectedChoice, setSelectedChoice] = useState<number | null>(null);

  // 선택지 설명 (시각장애인용)
  const describeChoice = (choice: Choice) => {
    const description = `
      ${choice.number}번 선택지: ${choice.text}
      핵심 주장: ${choice.coreClaim}
      ${choice.isCorrect ? '정답입니다.' : `오류 유형: ${choice.errorType}. ${choice.evidenceSentence}`}
    `;
    speak(description);
  };

  return (
    <div className="space-y-4">
      {/* 보호자용 시각 테이블 */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">선택지</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">핵심 주장</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">오류 유형</th>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">근거 문장</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {choices.map((choice) => (
                <tr
                  key={choice.number}
                  className={`hover:bg-gray-50 cursor-pointer transition-colors ${
                    choice.isCorrect ? 'bg-green-50' : 'bg-white'
                  } ${selectedChoice === choice.number ? 'ring-2 ring-blue-500' : ''}`}
                  onClick={() => {
                    setSelectedChoice(choice.number);
                    describeChoice(choice);
                  }}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {choice.isCorrect ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <XCircle className="w-5 h-5 text-gray-400" />
                      )}
                      <span className="font-medium text-gray-800">
                        {choice.number}번
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-800">{choice.coreClaim}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        choice.errorType === 'none'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {choice.errorType === 'none' ? '정답' : choice.errorType}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600 text-xs">
                    {choice.evidenceSentence}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 시각장애인용 음성 안내 버튼 */}
      <div className="bg-blue-50 rounded-lg p-4">
        <p className="text-sm text-gray-700 mb-3">
          선택지를 클릭하면 음성으로 설명을 들을 수 있습니다.
        </p>
        <div className="flex gap-2 flex-wrap">
          {choices.map((choice) => (
            <button
              key={choice.number}
              onClick={() => {
                stopTTS();
                describeChoice(choice);
              }}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm"
              aria-label={`${choice.number}번 선택지 설명 듣기`}
            >
              {choice.number}번 설명
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

