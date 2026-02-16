/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                neon: {
                    purple: '#A855F7',
                    blue: '#3B82F6',
                    dark: '#0F172A',
                    overlay: '#1E293B',
                },
                claro: {
                    red: '#EF3340',
                }
            },
            animation: {
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            },
            backdropBlur: {
                xs: '2px',
            }
        },
    },
    plugins: [],
}
