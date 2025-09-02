// API Configuration for Docker environment
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://172.19.0.3:8000',
  TIMEOUT: 30000,
  HEADERS: {
    'Content-Type': 'application/json',
  },
};

// Backward compatibility
export const API_BASE_URL = API_CONFIG.BASE_URL;

// Helper function for API calls
export const getApiUrl = (endpoint: string) => {
  if (endpoint.startsWith('/')) {
    return `${API_CONFIG.BASE_URL}${endpoint}`;
  }
  return `${API_CONFIG.BASE_URL}/${endpoint}`;
};

// Docker container network için özel ayarlar
export const DOCKER_CONFIG = {
  FRONTEND_HOST: process.env.NEXT_PUBLIC_FRONTEND_HOST || '172.19.0.2',
  FRONTEND_PORT: process.env.NEXT_PUBLIC_FRONTEND_PORT || '3000',
  BACKEND_HOST: process.env.NEXT_PUBLIC_BACKEND_HOST || '172.19.0.3',
  BACKEND_PORT: process.env.NEXT_PUBLIC_BACKEND_PORT || '8000',
};

// Environment detection
export const isDockerEnvironment = () => {
  return process.env.NODE_ENV === 'production' && 
         API_CONFIG.BASE_URL.includes('172.19.0.');
};

// Fetch wrapper with proper error handling for Docker environment
export const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
  const url = getApiUrl(endpoint);
  
  const defaultOptions: RequestInit = {
    ...options,
    headers: {
      ...API_CONFIG.HEADERS,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, defaultOptions);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response;
  } catch (error) {
    console.error(`API Request failed for ${url}:`, error);
    throw error;
  }
};
