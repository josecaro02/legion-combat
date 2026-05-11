import { createContext, useContext, useState, useEffect } from 'react';
import { clearAuth as clearAuthApi, isTokenExpired } from '../api/auth';
import { AUTH_TOKEN_KEY, REFRESH_TOKEN_KEY, USER_KEY, EXPIRY_KEY } from '../auth/constants';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [initError, setInitError] = useState(false);

  // Load from localStorage on mount - Ultra-robusto
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedToken = localStorage.getItem(AUTH_TOKEN_KEY);
        const storedUser = localStorage.getItem(USER_KEY);
        const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

        // Validación completa: deben existir todos los datos necesarios
        const hasAllTokens = storedToken && storedRefreshToken && storedUser;
        const isExpired = isTokenExpired();

        if (!hasAllTokens || isExpired) {
          // Faltan datos o está expirado → logout limpio
          clearAuthApi(false); // false = no redirect, lo hará el useEffect final
          setInitError(false);
          setLoading(false);
          return;
        }

        // Validar que el JSON del usuario sea válido
        let parsedUser;
        try {
          parsedUser = JSON.parse(storedUser);
          if (!parsedUser.id || !parsedUser.email || !parsedUser.role) {
            throw new Error('User data missing required fields');
          }
        } catch (e) {
          // JSON corrupto o datos incompletos
          clearAuthApi(false);
          setInitError(false);
          setLoading(false);
          return;
        }

        // Todo válido → cargar en estado
        setToken(storedToken);
        setUser(parsedUser);
        setInitError(false);
      } catch (error) {
        // Cualquier error inesperado → logout limpio
        console.error('Auth initialization error:', error);
        clearAuthApi(false);
        setInitError(true);
        setLoading(false);
      } finally {
        // Pequeño delay para evitar flicker de loading
        setTimeout(() => setLoading(false), 100);
      }
    };

    initializeAuth();
  }, []);

  // Si hubo error de inicialización, redirigir después del loading
  useEffect(() => {
    if (!loading && initError) {
      clearAuthApi(true);
    }
  }, [loading, initError]);

  const login = (newToken, newUser) => {
    // Guardar user en localStorage
    localStorage.setItem(USER_KEY, JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    clearAuthApi(true);
    setToken(null);
    setUser(null);
  };

  const isAuthenticated = !!token;

  // Valor del contexto
  const value = {
    token,
    user,
    login,
    logout,
    isAuthenticated,
    loading,
    // Propiedades adicionales para casos avanzados
    isInitialized: !loading,
    isError: initError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
