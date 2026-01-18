/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx,css}',
  ],
  theme: {
    extend: {
      colors: {
        // RGB with <alpha-value> placeholder → bg-primary/90 가능
        primary: 'rgb(49 130 246 / <alpha-value>)',   // #3182F6
        accent:  'rgb(42 193 188 / <alpha-value>)',   // #2AC1BC
        sky:     'rgb(108 202 255 / <alpha-value>)',  // #6CCAFF
        success: 'rgb(34 197 94 / <alpha-value>)',    // #22C55E
        danger:  'rgb(229 72 77 / <alpha-value>)',    // #E5484D
        muted:   'rgb(107 114 128 / <alpha-value>)',  // #6B7280
        border:  'rgb(229 231 235 / <alpha-value>)',  // #E5E7EB
        card:    'rgb(249 250 251 / <alpha-value>)',  // #F9FAFB
        fg:      'rgb(30 30 30 / <alpha-value>)',     // #1E1E1E
        bg:      'rgb(255 255 255 / <alpha-value>)',  // #FFFFFF
        
        // 기존 색상 유지 (하위 호환성)
        brand: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        }
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.25rem', // 토스 스타일
        '3xl': '1.5rem',
      },
      boxShadow: {
        'card': '0 8px 24px rgba(0,0,0,0.06)',
        'toss': '0 2px 8px rgba(0, 0, 0, 0.08)',
        'toss-lg': '0 4px 16px rgba(0, 0, 0, 0.12)',
      },
      fontSize: {
        'base': '16px', // 라이트 테마에서 조금 작게
        'lg': '18px',
        'xl': '20px',
        '2xl': '24px',
        '3xl': '28px',
      },
      spacing: {
        '18': '4.5rem', // 72px - 큰 터치 타겟
        '20': '5rem',   // 80px
      },
      minHeight: {
        '12': '3rem', // 48px - 최소 터치 타겟
      }
    },
  },
  plugins: [],
}