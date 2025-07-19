import axios from 'axios';

// Configuração base do Axios
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token de autenticação
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para tratamento de erros
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Tratar erro de autenticação
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // Redirecionar para login apenas se não estiver em uma página pública
      const publicPaths = ['/login', '/register', '/'];
      const currentPath = window.location.pathname;
      
      if (!publicPaths.includes(currentPath)) {
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;