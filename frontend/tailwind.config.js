/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans:   ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        outfit: ['Outfit', 'Inter', 'sans-serif'],
      },
      colors: {
        primary:        ({ opacityValue }) => opacityValue ? `hsl(var(--primary) / ${opacityValue})` : `hsl(var(--primary))`,
        'primary-hover':({ opacityValue }) => opacityValue ? `hsl(var(--primary-hover) / ${opacityValue})` : `hsl(var(--primary-hover))`,
        secondary:      ({ opacityValue }) => opacityValue ? `hsl(var(--secondary) / ${opacityValue})` : `hsl(var(--secondary))`,
        success:        ({ opacityValue }) => opacityValue ? `hsl(var(--success) / ${opacityValue})` : `hsl(var(--success))`,
        warning:        ({ opacityValue }) => opacityValue ? `hsl(var(--warning) / ${opacityValue})` : `hsl(var(--warning))`,
        error:          ({ opacityValue }) => opacityValue ? `hsl(var(--error) / ${opacityValue})` : `hsl(var(--error))`,
      },
      textColor: {
        main:      ({ opacityValue }) => opacityValue ? `hsl(var(--text-main) / ${opacityValue})` : `hsl(var(--text-main))`,
        muted:     ({ opacityValue }) => opacityValue ? `hsl(var(--text-muted) / ${opacityValue})` : `hsl(var(--text-muted))`,
        inverse:   ({ opacityValue }) => opacityValue ? `hsl(var(--text-inverse) / ${opacityValue})` : `hsl(var(--text-inverse))`,
        primary:   ({ opacityValue }) => opacityValue ? `hsl(var(--primary) / ${opacityValue})` : `hsl(var(--primary))`,
        secondary: ({ opacityValue }) => opacityValue ? `hsl(var(--secondary) / ${opacityValue})` : `hsl(var(--secondary))`,
        success:   ({ opacityValue }) => opacityValue ? `hsl(var(--success) / ${opacityValue})` : `hsl(var(--success))`,
        warning:   ({ opacityValue }) => opacityValue ? `hsl(var(--warning) / ${opacityValue})` : `hsl(var(--warning))`,
        error:     ({ opacityValue }) => opacityValue ? `hsl(var(--error) / ${opacityValue})` : `hsl(var(--error))`,
      },
      backgroundColor: {
        main:           ({ opacityValue }) => opacityValue ? `hsl(var(--bg-main) / ${opacityValue})` : `hsl(var(--bg-main))`,
        surface:        ({ opacityValue }) => opacityValue ? `hsl(var(--bg-surface) / ${opacityValue})` : `hsl(var(--bg-surface))`,
        subtle:         ({ opacityValue }) => opacityValue ? `hsl(var(--bg-subtle) / ${opacityValue})` : `hsl(var(--bg-subtle))`,
        primary:        ({ opacityValue }) => opacityValue ? `hsl(var(--primary) / ${opacityValue})` : `hsl(var(--primary))`,
        'primary-hover':({ opacityValue }) => opacityValue ? `hsl(var(--primary-hover) / ${opacityValue})` : `hsl(var(--primary-hover))`,
        secondary:      ({ opacityValue }) => opacityValue ? `hsl(var(--secondary) / ${opacityValue})` : `hsl(var(--secondary))`,
        success:        ({ opacityValue }) => opacityValue ? `hsl(var(--success) / ${opacityValue})` : `hsl(var(--success))`,
        warning:        ({ opacityValue }) => opacityValue ? `hsl(var(--warning) / ${opacityValue})` : `hsl(var(--warning))`,
        error:          ({ opacityValue }) => opacityValue ? `hsl(var(--error) / ${opacityValue})` : `hsl(var(--error))`,
      },
      borderColor: {
        base:      ({ opacityValue }) => opacityValue ? `hsl(var(--border-base) / ${opacityValue})` : `hsl(var(--border-base))`,
        focus:     ({ opacityValue }) => opacityValue ? `hsl(var(--border-focus) / ${opacityValue})` : `hsl(var(--border-focus))`,
        primary:   ({ opacityValue }) => opacityValue ? `hsl(var(--primary) / ${opacityValue})` : `hsl(var(--primary))`,
        secondary: ({ opacityValue }) => opacityValue ? `hsl(var(--secondary) / ${opacityValue})` : `hsl(var(--secondary))`,
        success:   ({ opacityValue }) => opacityValue ? `hsl(var(--success) / ${opacityValue})` : `hsl(var(--success))`,
        warning:   ({ opacityValue }) => opacityValue ? `hsl(var(--warning) / ${opacityValue})` : `hsl(var(--warning))`,
        error:     ({ opacityValue }) => opacityValue ? `hsl(var(--error) / ${opacityValue})` : `hsl(var(--error))`,
      },
      ringColor: {
        primary: ({ opacityValue }) => opacityValue ? `hsl(var(--primary) / ${opacityValue})` : `hsl(var(--primary))`,
        focus:   ({ opacityValue }) => opacityValue ? `hsl(var(--border-focus) / ${opacityValue})` : `hsl(var(--border-focus))`,
      },
      ringOffsetColor: {
        main: ({ opacityValue }) => opacityValue ? `hsl(var(--bg-main) / ${opacityValue})` : `hsl(var(--bg-main))`,
      },
      boxShadowColor: {
        primary:   ({ opacityValue }) => opacityValue ? `hsl(var(--primary) / ${opacityValue})` : `hsl(var(--primary))`,
        secondary: ({ opacityValue }) => opacityValue ? `hsl(var(--secondary) / ${opacityValue})` : `hsl(var(--secondary))`,
        success:   ({ opacityValue }) => opacityValue ? `hsl(var(--success) / ${opacityValue})` : `hsl(var(--success))`,
        error:     ({ opacityValue }) => opacityValue ? `hsl(var(--error) / ${opacityValue})` : `hsl(var(--error))`,
      },
    },
  },
  plugins: [],
}
