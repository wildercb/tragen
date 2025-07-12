// Trading Agent Theme Colors
// Robin Egg Blue, Dim Grey, and Eerie Black color scheme

export const colors = {
  // Primary Colors
  primary: {
    50: '#f0fdfa',   // Lightest robin egg blue
    100: '#ccfbf1',  // Very light robin egg blue
    200: '#99f6e4',  // Light robin egg blue
    300: '#5eead4',  // Robin egg blue
    400: '#2dd4bf',  // Medium robin egg blue
    500: '#14b8a6',  // Main robin egg blue
    600: '#0d9488',  // Darker robin egg blue
    700: '#0f766e',  // Dark robin egg blue
    800: '#115e59',  // Very dark robin egg blue
    900: '#134e4a',  // Darkest robin egg blue
  },
  
  // Grey Scale (Dim Grey variations)
  grey: {
    50: '#f9fafb',   // Lightest grey
    100: '#f3f4f6',  // Very light grey
    200: '#e5e7eb',  // Light grey
    300: '#d1d5db',  // Medium light grey
    400: '#9ca3af',  // Medium grey
    500: '#6b7280',  // Dim grey (base)
    600: '#4b5563',  // Darker dim grey
    700: '#374151',  // Dark grey
    800: '#1f2937',  // Very dark grey
    900: '#111827',  // Darkest grey
  },
  
  // Background Colors (Eerie Black variations)
  background: {
    primary: '#0a0a0b',    // Eerie black (main background)
    secondary: '#141517',   // Slightly lighter eerie black
    tertiary: '#1e2023',    // Card backgrounds
    quaternary: '#282b30',  // Elevated elements
    overlay: '#0a0a0b99',   // Semi-transparent overlay
  },
  
  // Text Colors
  text: {
    primary: '#f9fafb',     // Primary text (light grey)
    secondary: '#d1d5db',   // Secondary text
    tertiary: '#9ca3af',    // Tertiary text
    muted: '#6b7280',       // Muted text
    inverse: '#0a0a0b',     // Dark text on light backgrounds
  },
  
  // Status Colors
  status: {
    success: '#10b981',     // Green for profits/success
    danger: '#ef4444',      // Red for losses/danger
    warning: '#f59e0b',     // Orange for warnings
    info: '#3b82f6',        // Blue for information
  },
  
  // Trading Specific Colors
  trading: {
    buy: '#10b981',         // Buy signal green
    sell: '#ef4444',        // Sell signal red
    profit: '#059669',      // Profit green
    loss: '#dc2626',        // Loss red
    neutral: '#6b7280',     // Neutral/no position
    pending: '#f59e0b',     // Pending order orange
  },
  
  // Chart Colors
  chart: {
    bullish: '#10b981',     // Green candles
    bearish: '#ef4444',     // Red candles
    volume: '#14b8a6',      // Volume bars (robin egg blue)
    indicators: {
      sma: '#f59e0b',       // Simple moving average
      ema: '#8b5cf6',       // Exponential moving average
      rsi: '#06b6d4',       // RSI
      macd: '#ec4899',      // MACD
      bollinger: '#10b981', // Bollinger bands
    },
    grid: '#374151',        // Chart grid lines
    axis: '#6b7280',        // Chart axis
  },
  
  // Border Colors
  border: {
    light: '#374151',       // Light borders
    medium: '#4b5563',      // Medium borders
    dark: '#1f2937',        // Dark borders
    accent: '#14b8a6',      // Accent borders (robin egg blue)
  },
  
  // Interactive Elements
  interactive: {
    hover: '#14b8a620',     // Hover state (robin egg blue with opacity)
    active: '#14b8a640',    // Active state
    focus: '#14b8a6',       // Focus ring
    disabled: '#6b7280',    // Disabled state
  }
};

// CSS Custom Properties for easy theme switching
export const cssVariables = {
  '--color-primary': colors.primary[500],
  '--color-primary-light': colors.primary[400],
  '--color-primary-dark': colors.primary[600],
  
  '--color-background': colors.background.primary,
  '--color-background-secondary': colors.background.secondary,
  '--color-background-tertiary': colors.background.tertiary,
  
  '--color-text-primary': colors.text.primary,
  '--color-text-secondary': colors.text.secondary,
  '--color-text-muted': colors.text.muted,
  
  '--color-border': colors.border.light,
  '--color-border-accent': colors.border.accent,
  
  '--color-success': colors.status.success,
  '--color-danger': colors.status.danger,
  '--color-warning': colors.status.warning,
  
  '--color-buy': colors.trading.buy,
  '--color-sell': colors.trading.sell,
  '--color-profit': colors.trading.profit,
  '--color-loss': colors.trading.loss,
};

// Tailwind CSS color extensions
export const tailwindColors = {
  'robin-egg': colors.primary,
  'dim-grey': colors.grey,
  'eerie-black': colors.background,
  'trading-buy': colors.trading.buy,
  'trading-sell': colors.trading.sell,
  'trading-profit': colors.trading.profit,
  'trading-loss': colors.trading.loss,
};

export default colors;