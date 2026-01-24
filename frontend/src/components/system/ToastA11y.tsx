import { useEffect } from 'react';

interface ToastA11yProps {
  message: string;
  isVisible: boolean;
  duration?: number;
  onClose: () => void;
  position?: 'top' | 'bottom';
}

export default function ToastA11y({
  message,
  isVisible,
  duration = 3000,
  onClose,
  position = 'top',
}: ToastA11yProps) {
  useEffect(() => {
    if (isVisible && duration > 0) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [isVisible, duration, onClose]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (isVisible && e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isVisible, onClose]);

  if (!isVisible) return null;

  return (
    <div
      className={`
        fixed ${position === 'top' ? 'top-4' : 'bottom-4'}
        left-1/2 transform -translate-x-1/2 z-50
        bg-black text-white px-4 py-2 rounded-lg shadow-lg
        transition-opacity duration-300
        ${isVisible ? 'opacity-100' : 'opacity-0'}
      `}
      role="alert"
      aria-live="polite"
    >
      {message}
    </div>
  );
}
