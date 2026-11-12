export const USE_MOCK = import.meta.env.VITE_USE_MOCK !== undefined 
  ? import.meta.env.VITE_USE_MOCK === 'true' 
  : false;

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://payguard-ai-izry.onrender.com';
export const EXTRAS_API_URL = import.meta.env.VITE_EXTRAS_API_URL || API_BASE_URL;

