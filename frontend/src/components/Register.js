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
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import { Egg as EggIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const steps = ['Данные аккаунта', 'Контрольный вопрос'];

const Register = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [securityQuestion, setSecurityQuestion] = useState('');
  const [securityAnswer, setSecurityAnswer] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleNext = async () => {
    if (activeStep === 0) {
      if (!username || !password || !confirmPassword) {
        setError('Заполните все поля');
        return;
      }
      if (password.length < 6) {
        setError('Пароль должен быть не менее 6 символов');
        return;
      }
      if (password !== confirmPassword) {
        setError('Пароли не совпадают');
        return;
      }
      setError('');
      setActiveStep(1);
    } else {
      if (!securityQuestion || !securityAnswer) {
        setError('Заполните все поля');
        return;
      }
      setError('');
      setLoading(true);

      try {
        await register(username, password, securityQuestion, securityAnswer);
        setSuccess(true);
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } catch (err) {
        setError(err.response?.data?.error || 'Ошибка регистрации');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
    setError('');
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
              Регистрация нового аккаунта
            </Typography>
          </Box>

          {!success ? (
            <>
              <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
                {steps.map((label) => (
                  <Step key={label}>
                    <StepLabel>{label}</StepLabel>
                  </Step>
                ))}
              </Stepper>

              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              {activeStep === 0 && (
                <Box>
                  <TextField
                    fullWidth
                    label="Имя пользователя"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    margin="normal"
                    required
                  />
                  <TextField
                    fullWidth
                    label="Пароль"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    margin="normal"
                    required
                    helperText="Минимум 6 символов"
                  />
                  <TextField
                    fullWidth
                    label="Подтверждение пароля"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    margin="normal"
                    required
                  />
                </Box>
              )}

              {activeStep === 1 && (
                <Box>
                  <TextField
                    fullWidth
                    label="Секретный вопрос"
                    value={securityQuestion}
                    onChange={(e) => setSecurityQuestion(e.target.value)}
                    margin="normal"
                    required
                    placeholder="Например: Девичья фамилия матери?"
                  />
                  <TextField
                    fullWidth
                    label="Ответ на секретный вопрос"
                    value={securityAnswer}
                    onChange={(e) => setSecurityAnswer(e.target.value)}
                    margin="normal"
                    required
                    type="password"
                  />
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    Этот вопрос поможет восстановить пароль, если вы его забудете.
                  </Typography>
                </Box>
              )}

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                {activeStep === 1 && (
                  <Button onClick={handleBack} disabled={loading}>
                    Назад
                  </Button>
                )}
                <Button
                  variant="contained"
                  onClick={handleNext}
                  disabled={loading}
                >
                  {activeStep === steps.length - 1 ? (loading ? 'Регистрация...' : 'Зарегистрироваться') : 'Далее'}
                </Button>
              </Box>
            </>
          ) : (
            <Alert severity="success" sx={{ textAlign: 'center' }}>
              Аккаунт успешно создан! Перенаправление...
            </Alert>
          )}

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2">
              Уже есть аккаунт?{' '}
              <MuiLink component={Link} to="/login" underline="hover">
                Войти
              </MuiLink>
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default Register;
