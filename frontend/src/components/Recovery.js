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
import { LockReset as LockResetIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const steps = ['Поиск аккаунта', 'Контрольный вопрос', 'Новый пароль'];

const Recovery = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [username, setUsername] = useState('');
  const [securityQuestion, setSecurityQuestion] = useState('');
  const [securityAnswer, setSecurityAnswer] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const { recoveryQuestion, resetPassword } = useAuth();
  const navigate = useNavigate();

  const handleNext = async () => {
    if (activeStep === 0) {
      if (!username) {
        setError('Введите имя пользователя');
        return;
      }
      setError('');
      setLoading(true);

      try {
        const data = await recoveryQuestion(username);
        setSecurityQuestion(data.security_question);
        setActiveStep(1);
      } catch (err) {
        setError(err.response?.data?.error || 'Пользователь не найден');
      } finally {
        setLoading(false);
      }
    } else if (activeStep === 1) {
      if (!securityAnswer) {
        setError('Введите ответ на секретный вопрос');
        return;
      }
      setError('');
      setActiveStep(2);
    } else {
      if (!newPassword || !confirmPassword) {
        setError('Заполните все поля');
        return;
      }
      if (newPassword.length < 6) {
        setError('Пароль должен быть не менее 6 символов');
        return;
      }
      if (newPassword !== confirmPassword) {
        setError('Пароли не совпадают');
        return;
      }
      setError('');
      setLoading(true);

      try {
        await resetPassword(username, securityAnswer, newPassword);
        setSuccess(true);
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } catch (err) {
        setError(err.response?.data?.error || 'Ошибка сброса пароля');
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
            <LockResetIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" component="h1" gutterBottom>
              Восстановление пароля
            </Typography>
            <Typography variant="body2" color="text.secondary">
              🐔 Десять курочек
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
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    Введите имя пользователя, чтобы найти ваш аккаунт.
                  </Typography>
                </Box>
              )}

              {activeStep === 1 && (
                <Box>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {securityQuestion}
                  </Typography>
                  <TextField
                    fullWidth
                    label="Ваш ответ"
                    value={securityAnswer}
                    onChange={(e) => setSecurityAnswer(e.target.value)}
                    margin="normal"
                    required
                    type="password"
                  />
                </Box>
              )}

              {activeStep === 2 && (
                <Box>
                  <TextField
                    fullWidth
                    label="Новый пароль"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    margin="normal"
                    required
                    helperText="Минимум 6 символов"
                  />
                  <TextField
                    fullWidth
                    label="Подтверждение нового пароля"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    margin="normal"
                    required
                  />
                </Box>
              )}

              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
                {activeStep > 0 && (
                  <Button onClick={handleBack} disabled={loading}>
                    Назад
                  </Button>
                )}
                <Button
                  variant="contained"
                  onClick={handleNext}
                  disabled={loading}
                >
                  {activeStep === steps.length - 1 ? (loading ? 'Сброс пароля...' : 'Сбросить пароль') : 'Далее'}
                </Button>
              </Box>
            </>
          ) : (
            <Alert severity="success" sx={{ textAlign: 'center' }}>
              Пароль успешно изменен! Перенаправление...
            </Alert>
          )}

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2">
              Вспомнили пароль?{' '}
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

export default Recovery;
