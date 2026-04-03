import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Alert,
  Link as MuiLink,
} from '@mui/material';
import { Egg as EggIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
            <EggIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" component="h1" gutterBottom>
              🐔 Десять курочек
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Вход в систему
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Имя пользователя"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              margin="normal"
              required
              autoComplete="username"
            />
            <TextField
              fullWidth
              label="Пароль"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              required
              autoComplete="current-password"
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading}
              sx={{ mt: 3, mb: 2 }}
            >
              {loading ? 'Вход...' : 'Войти'}
            </Button>
            <Box sx={{ textAlign: 'center' }}>
              <MuiLink component={Link} to="/recovery" underline="hover">
                Забыли пароль?
              </MuiLink>
            </Box>
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Typography variant="body2">
                Нет аккаунта?{' '}
                <MuiLink component={Link} to="/register" underline="hover">
                  Зарегистрироваться
                </MuiLink>
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;
