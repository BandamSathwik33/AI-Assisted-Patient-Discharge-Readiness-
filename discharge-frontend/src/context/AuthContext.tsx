import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, UserRole } from '../types';
import { apiClient } from '../api/client';
import { DEMO_USERS } from '../mock/mockData';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password?: string) => Promise<void>;
  quickLogin: (username: string) => Promise<void>;
  switchRole: (role: UserRole) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedUser = localStorage.getItem('discharge_user');
        if (storedUser) {
          setUser(JSON.parse(storedUser));
        } else {
          // Default to Dr. Smith for smooth initial load
          const defaultUser = DEMO_USERS['dr.smith'];
          setUser(defaultUser);
          localStorage.setItem('discharge_user', JSON.stringify(defaultUser));
        }
      } catch (err) {
        console.error('Auth initialization error:', err);
      } finally {
        setLoading(false);
      }
    };
    initAuth();
  }, []);

  const login = async (username: string, password?: string) => {
    setLoading(true);
    try {
      const authResp = await apiClient.login(username, password);
      const newUser: User = {
        user_id: authResp.user_id,
        username: username,
        full_name: authResp.full_name,
        role: authResp.role,
        token: authResp.access_token,
      };
      setUser(newUser);
      localStorage.setItem('discharge_user', JSON.stringify(newUser));
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = async (userKey: string) => {
    setLoading(true);
    try {
      const targetUser = DEMO_USERS[userKey] || DEMO_USERS['dr.smith'];
      const authResp = await apiClient.login(targetUser.username, 'demo123');
      const newUser: User = {
        user_id: authResp.user_id,
        username: targetUser.username,
        full_name: authResp.full_name,
        role: authResp.role,
        token: authResp.access_token,
      };
      setUser(newUser);
      localStorage.setItem('discharge_user', JSON.stringify(newUser));
    } finally {
      setLoading(false);
    }
  };

  const switchRole = (newRole: UserRole) => {
    if (!user) return;
    const updated = { ...user, role: newRole };
    setUser(updated);
    localStorage.setItem('discharge_user', JSON.stringify(updated));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('discharge_auth_token');
    localStorage.removeItem('discharge_user');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, quickLogin, switchRole, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
