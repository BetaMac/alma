interface Config {
  apiUrl: string;
  wsUrl: string;
  enableAnalytics: boolean;
  enableDebugMode: boolean;
  maxInputLength: number;
  defaultTimeout: number;
}

class ConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationError';
  }
}

function validateUrl(url: string, type: 'API' | 'WebSocket'): string {
  try {
    const parsed = new URL(url);
    if (type === 'WebSocket' && !['ws:', 'wss:'].includes(parsed.protocol)) {
      throw new Error(`WebSocket URL must use ws:// or wss:// protocol`);
    }
    if (type === 'API' && !['http:', 'https:'].includes(parsed.protocol)) {
      throw new Error(`API URL must use http:// or https:// protocol`);
    }
    return url;
  } catch (error) {
    throw new ConfigurationError(`Invalid ${type} URL: ${error.message}`);
  }
}

function validateNumber(value: number, min: number, max: number, name: string): number {
  if (value < min || value > max) {
    throw new ConfigurationError(`${name} must be between ${min} and ${max}`);
  }
  return value;
}

function loadConfig(): Config {
  const config = {
    apiUrl: validateUrl(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000', 'API'),
    wsUrl: validateUrl(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000', 'WebSocket'),
    enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
    enableDebugMode: process.env.NEXT_PUBLIC_ENABLE_DEBUG_MODE === 'true',
    maxInputLength: validateNumber(
      parseInt(process.env.NEXT_PUBLIC_MAX_INPUT_LENGTH || '2000', 10),
      100,
      10000,
      'Max input length'
    ),
    defaultTimeout: validateNumber(
      parseInt(process.env.NEXT_PUBLIC_DEFAULT_TIMEOUT || '600', 10),
      30,
      3600,
      'Default timeout'
    ),
  };

  // Log configuration in debug mode
  if (config.enableDebugMode) {
    console.log('Frontend Configuration:', {
      ...config,
      // Mask sensitive values if needed
    });
  }

  return config;
}

// Export a frozen configuration object
export const config = Object.freeze(loadConfig());

// Type guard for runtime configuration checks
export function assertConfig(key: keyof Config): void {
  if (!(key in config)) {
    throw new ConfigurationError(`Missing configuration key: ${key}`);
  }
} 