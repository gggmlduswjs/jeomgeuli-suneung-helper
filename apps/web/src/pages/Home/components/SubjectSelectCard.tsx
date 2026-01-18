/**
 * 과목 선택 카드
 * 보호자용 시각 UI + 시각장애인용 음성 명령
 */
import { useNavigate } from 'react-router-dom';
import { BookOpen, Globe, Calculator } from 'lucide-react';

interface SubjectSelectCardProps {
  onSubjectSelect?: (subject: 'korean' | 'english' | 'math') => void;
}

export default function SubjectSelectCard({ onSubjectSelect }: SubjectSelectCardProps) {
  const navigate = useNavigate();

  const subjects = [
    {
      id: 'korean' as const,
      name: '국어',
      icon: BookOpen,
      color: 'from-red-50 to-red-100',
      borderColor: 'border-red-200',
      iconColor: 'text-red-600'
    },
    {
      id: 'english' as const,
      name: '영어',
      icon: Globe,
      color: 'from-blue-50 to-blue-100',
      borderColor: 'border-blue-200',
      iconColor: 'text-blue-600'
    },
    {
      id: 'math' as const,
      name: '수학',
      icon: Calculator,
      color: 'from-green-50 to-green-100',
      borderColor: 'border-green-200',
      iconColor: 'text-green-600'
    }
  ];

  const handleSubjectClick = (subject: 'korean' | 'english' | 'math') => {
    if (onSubjectSelect) {
      onSubjectSelect(subject);
    } else {
      navigate(`/textbook?subject=${subject}`);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border-2 border-gray-200">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">과목 선택</h3>
      
      <div className="grid grid-cols-3 gap-4">
        {subjects.map((subject) => {
          const Icon = subject.icon;
          return (
            <button
              key={subject.id}
              onClick={() => handleSubjectClick(subject.id)}
              className={`bg-gradient-to-br ${subject.color} rounded-lg p-4 border-2 ${subject.borderColor} hover:shadow-lg transition-all transform hover:scale-105`}
              aria-label={`${subject.name} 선택`}
            >
              <Icon className={`w-8 h-8 ${subject.iconColor} mx-auto mb-2`} />
              <p className="text-sm font-medium text-gray-800">{subject.name}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}

