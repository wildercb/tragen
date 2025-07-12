module.exports = {
  extends: ['react-app', 'react-app/jest'],
  rules: {
    // Disable exhaustive-deps rule for useEffect and useCallback
    'react-hooks/exhaustive-deps': 'off',
    // Allow unused variables (for imports that are used in JSX)
    'no-unused-vars': 'warn',
  },
};