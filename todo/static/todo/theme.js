// ダークモード/ライトモード切り替え機能

(function() {
  // システムの設定を確認してテーマを初期化
  function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme) {
      // 保存されたテーマがあればそれを使用
      applyTheme(savedTheme);
    } else if (prefersDark) {
      // システム設定がダークモードの場合
      applyTheme('dark');
    } else {
      // デフォルトはライトモード
      applyTheme('light');
    }
    
    // テーマトグルボタンを初期化
    initializeThemeToggle();
  }
  
  // テーマを適用
  function applyTheme(theme) {
    if (theme === 'dark') {
      document.documentElement.style.colorScheme = 'dark';
      localStorage.setItem('theme', 'dark');
      updateThemeToggleButton('dark');
    } else {
      document.documentElement.style.colorScheme = 'light';
      localStorage.setItem('theme', 'light');
      updateThemeToggleButton('light');
    }
  }
  
  // テーマトグルボタンを初期化
  function initializeThemeToggle() {
    const button = document.getElementById('theme-toggle');
    if (button) {
      button.addEventListener('click', toggleTheme);
    }
  }
  
  // テーマを切り替え
  function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
  }
  
  // テーマトグルボタンのアイコンを更新
  function updateThemeToggleButton(theme) {
    const button = document.getElementById('theme-toggle');
    if (button) {
      if (theme === 'dark') {
        button.textContent = '☀️'; // 日中のアイコン（ダークモード時）
        button.title = 'ライトモードに切り替え';
      } else {
        button.textContent = '🌙'; // 月のアイコン（ライトモード時）
        button.title = 'ダークモードに切り替え';
      }
    }
  }
  
  // システムのダークモード設定が変更された時の処理
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const savedTheme = localStorage.getItem('theme');
    if (!savedTheme) {
      // ユーザーがテーマを手動設定していない場合、システム設定に従う
      applyTheme(e.matches ? 'dark' : 'light');
    }
  });
  
  // DOMContentLoaded時に初期化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTheme);
  } else {
    initializeTheme();
  }
})();
