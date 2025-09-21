/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './finflow/**/*.{html,js}',
    './finflow/core/**/*.{html,js}',
    './templates/**/*.html',
    './static/**/*.js',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
