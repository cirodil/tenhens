import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || '';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/auth/me`);
      setUser(response.data.user);
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    const response = await axios.post(`${API_URL}/api/auth/login`, {
      username,
      password,
    });
    const { access_token, user } = response.data;
    localStorage.setItem('token', access_token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    setUser(user);
    return response.data;
  };

  const register = async (username, password, securityQuestion, securityAnswer) => {
    const response = await axios.post(`${API_URL}/api/auth/register`, {
      username,
      password,
      security_question: securityQuestion,
      security_answer: securityAnswer,
    });
    return response.data;
  };

  const recoveryQuestion = async (username) => {
    const response = await axios.post(`${API_URL}/api/auth/recovery-question`, {
      username,
    });
    return response.data;
  };

  const resetPassword = async (username, securityAnswer, newPassword) => {
    const response = await axios.post(`${API_URL}/api/auth/reset-password`, {
      username,
      security_answer: securityAnswer,
      new_password: newPassword,
    });
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    recoveryQuestion,
    resetPassword,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
