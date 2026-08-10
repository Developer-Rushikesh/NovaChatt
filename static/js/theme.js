/**
 * NovaChat Theme Manager & Custom Switcher Logic
 * Provides seamless Light Mode and Dark Mode switching with:
 * 1. Persistent preference in localStorage ('novachat_theme')
 * 2. Automatic OS system theme detection via prefers-color-scheme
 * 3. Multi-tab synchronization
 * 4. Zero Flash-of-Unstyled-Content (FOUC)
 */

(function () {
    // Key used for saving theme preference in browser localStorage
    const THEME_STORAGE_KEY = 'novachat_theme';

    /**
     * Determines the active theme based on localStorage override or OS system preferences.
     * @returns {'light' | 'dark'} Active theme string
     */
    function getPreferredTheme() {
        const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
        if (savedTheme === 'light' || savedTheme === 'dark') {
            return savedTheme;
        }
        // Fallback to system preference (prefers-color-scheme: dark)
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    /**
     * Applies the specified theme to the document <html> tag and updates UI switches.
     * @param {'light' | 'dark'} theme 
     */
    function applyTheme(theme) {
        // Set attribute on <html> element
        document.documentElement.setAttribute('data-theme', theme);
        
        // Also sync body background for legacy or inline components
        if (document.body) {
            document.body.setAttribute('data-theme', theme);
        }

        // Update all theme toggle buttons present on the page
        const toggleBtns = document.querySelectorAll('.theme-switch-btn');
        toggleBtns.forEach(btn => {
            btn.setAttribute('aria-checked', theme === 'dark' ? 'true' : 'false');
            btn.setAttribute('title', theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
        });
    }

    /**
     * Toggles theme between Light and Dark mode, saves choice to localStorage, and updates UI.
     */
    window.toggleTheme = function () {
        const currentTheme = document.documentElement.getAttribute('data-theme') || getPreferredTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        // Save user choice in localStorage
        localStorage.setItem(THEME_STORAGE_KEY, newTheme);
        
        // Apply theme to document
        applyTheme(newTheme);
    };

    // Apply theme immediately on script load to prevent FOUC
    const initialTheme = getPreferredTheme();
    document.documentElement.setAttribute('data-theme', initialTheme);

    // Re-apply theme and bind events once DOM content is loaded
    document.addEventListener('DOMContentLoaded', () => {
        applyTheme(getPreferredTheme());

        // Listen for OS system theme changes (if user hasn't explicitly set localStorage preference)
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem(THEME_STORAGE_KEY)) {
                applyTheme(e.matches ? 'dark' : 'light');
            }
        });

        // Sync theme changes across multiple open tabs
        window.addEventListener('storage', (e) => {
            if (e.key === THEME_STORAGE_KEY) {
                applyTheme(e.newValue || getPreferredTheme());
            }
        });
    });
})();
