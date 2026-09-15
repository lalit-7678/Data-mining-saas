/**
 * Theme Controller Utility
 */
export const AppTheme = {
  init() {
    const savedTheme = localStorage.getItem('app_theme') || 'light';
    this.setTheme(savedTheme);
  },

  setTheme(theme) {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('app_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('app_theme', 'light');
    }
  },

  toggle() {
    const currentTheme = localStorage.getItem('app_theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
    return newTheme;
  },

  getTheme() {
    return localStorage.getItem('app_theme') || 'light';
  }
};