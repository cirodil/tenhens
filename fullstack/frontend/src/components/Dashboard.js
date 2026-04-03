import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  CssBaseline,
  Container,
  Grid,
  Paper,
  Card,
  CardContent,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Slider,
  Metric,
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  Add as AddIcon,
  List as ListIcon,
  BarChart as BarChartIcon,
  Insights as InsightsIcon,
  ShowChart as ShowChartIcon,
  Logout as LogoutIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Close as CloseIcon,
  Egg as EggIcon,
  Assessment as AssessmentIcon,
  DonutLarge as DonutLargeIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const drawerWidth = 240;

const API_URL = process.env.REACT_APP_API_URL || '';

const Dashboard = () => {
  const [open, setOpen] = useState(true);
  const [selectedView, setSelectedView] = useState('records');
  const [summary, setSummary] = useState({ total_eggs: 0, records_count: 0, avg_per_record: 0 });
  const [records, setRecords] = useState([]);
  const [stats, setStats] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [plotUrl, setPlotUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  
  // Filter states
  const [minDate, setMinDate] = useState('');
  const [maxDate, setMaxDate] = useState('');
  const [searchNotes, setSearchNotes] = useState('');
  
  // Dialog states
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  
  // Form states
  const [newRecord, setNewRecord] = useState({ date: new Date().toISOString().split('T')[0], count: 0, notes: '' });
  const [editRecord, setEditRecord] = useState({ date: '', count: 0, notes: '' });
  const [analyticsDays, setAnalyticsDays] = useState(30);
  const [plotDays, setPlotDays] = useState(30);

  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const toggleDrawer = () => setOpen(!open);

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const fetchSummary = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/summary`);
      setSummary(response.data);
    } catch (err) {
      console.error('Error fetching summary:', err);
    }
  };

  const fetchRecords = async () => {
    try {
      const params = {};
      if (minDate) params.min_date = minDate;
      if (maxDate) params.max_date = maxDate;
      if (searchNotes) params.search_notes = searchNotes;
      
      const response = await axios.get(`${API_URL}/api/records`, { params });
      setRecords(response.data.records);
    } catch (err) {
      console.error('Error fetching records:', err);
    }
  };

  const fetchStats = async (days = 7) => {
    try {
      const response = await axios.get(`${API_URL}/api/stats`, { params: { days } });
      setStats(response.data.stats);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const fetchAnalytics = async (days = 30) => {
    try {
      const response = await axios.get(`${API_URL}/api/analytics`, { params: { days } });
      setAnalytics(response.data.analytics);
    } catch (err) {
      console.error('Error fetching analytics:', err);
    }
  };

  const fetchPlot = async (days = 30) => {
    try {
      const response = await axios.get(`${API_URL}/api/plot`, { 
        params: { days },
        responseType: 'blob'
      });
      const url = URL.createObjectURL(response.data);
      setPlotUrl(url);
    } catch (err) {
      console.error('Error fetching plot:', err);
      setPlotUrl('');
    }
  };

  useEffect(() => {
    fetchSummary();
    fetchRecords();
  }, []);

  useEffect(() => {
    if (selectedView === 'records') {
      fetchRecords();
    } else if (selectedView === 'stats') {
      fetchStats(7);
    } else if (selectedView === 'analytics') {
      fetchAnalytics(analyticsDays);
    } else if (selectedView === 'plot') {
      fetchPlot(plotDays);
    }
  }, [selectedView]);

  const handleAddRecord = async () => {
    if (!newRecord.date || newRecord.count <= 0) {
      showSnackbar('Заполните дату и количество яиц', 'error');
      return;
    }
    
    try {
      await axios.post(`${API_URL}/api/records`, newRecord);
      showSnackbar('Запись успешно добавлена!');
      setAddDialogOpen(false);
      setNewRecord({ date: new Date().toISOString().split('T')[0], count: 0, notes: '' });
      fetchSummary();
      fetchRecords();
    } catch (err) {
      showSnackbar(err.response?.data?.error || 'Ошибка добавления записи', 'error');
    }
  };

  const handleUpdateRecord = async () => {
    if (!selectedRecord) return;
    
    try {
      await axios.put(`${API_URL}/api/records/${selectedRecord.id}`, editRecord);
      showSnackbar('Запись успешно обновлена!');
      setEditDialogOpen(false);
      fetchRecords();
    } catch (err) {
      showSnackbar(err.response?.data?.error || 'Ошибка обновления записи', 'error');
    }
  };

  const handleDeleteRecord = async () => {
    if (!selectedRecord) return;
    
    try {
      await axios.delete(`${API_URL}/api/records/${selectedRecord.id}`);
      showSnackbar('Запись успешно удалена!');
      setDeleteDialogOpen(false);
      fetchSummary();
      fetchRecords();
    } catch (err) {
      showSnackbar(err.response?.data?.error || 'Ошибка удаления записи', 'error');
    }
  };

  const openEditDialog = (record) => {
    setSelectedRecord(record);
    setEditRecord({ date: record.date, count: record.count, notes: record.notes || '' });
    setEditDialogOpen(true);
  };

  const openDeleteDialog = (record) => {
    setSelectedRecord(record);
    setDeleteDialogOpen(true);
  };

  const handleExportCSV = () => {
    const headers = ['ID', 'Дата', 'Количество', 'Заметки'];
    const csvData = records.map(r => [r.id, r.date, r.count, r.notes || '']);
    const csv = [headers, ...csvData].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `egg_records_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  const menuItems = [
    { text: 'Записи', icon: <ListIcon />, view: 'records' },
    { text: 'Добавить запись', icon: <AddIcon />, view: 'add' },
    { text: 'Статистика', icon: <BarChartIcon />, view: 'stats' },
    { text: 'Аналитика', icon: <InsightsIcon />, view: 'analytics' },
    { text: 'График', icon: <ShowChartIcon />, view: 'plot' },
  ];

  const renderContent = () => {
    switch (selectedView) {
      case 'records':
        return (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5">📋 Управление записями</Typography>
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => setAddDialogOpen(true)}>
                Добавить запись
              </Button>
            </Box>

            {/* Filters */}
            <Paper sx={{ p: 2, mb: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="От даты"
                    type="date"
                    value={minDate}
                    onChange={(e) => setMinDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="До даты"
                    type="date"
                    value={maxDate}
                    onChange={(e) => setMaxDate(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Поиск по заметкам"
                    value={searchNotes}
                    onChange={(e) => setSearchNotes(e.target.value)}
                    size="small"
                  />
                </Grid>
              </Grid>
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button variant="outlined" size="small" onClick={fetchRecords}>Применить фильтры</Button>
                <Button variant="outlined" size="small" onClick={handleExportCSV}>Экспорт CSV</Button>
              </Box>
            </Paper>

            {/* Records Table */}
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Дата</TableCell>
                    <TableCell>Яиц</TableCell>
                    <TableCell>Заметки</TableCell>
                    <TableCell>Действия</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {records.map((record) => (
                    <TableRow key={record.id}>
                      <TableCell>{record.id}</TableCell>
                      <TableCell>{record.date}</TableCell>
                      <TableCell>{record.count} 🥚</TableCell>
                      <TableCell>{record.notes || '-'}</TableCell>
                      <TableCell>
                        <IconButton size="small" onClick={() => openEditDialog(record)}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton size="small" onClick={() => openDeleteDialog(record)}>
                          <DeleteIcon fontSize="small" color="error" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            {records.length === 0 && (
              <Typography sx={{ mt: 2, textAlign: 'center' }} color="text.secondary">
                Нет записей. Добавьте первую запись!
              </Typography>
            )}
          </Box>
        );

      case 'add':
        setTimeout(() => {
          setAddDialogOpen(true);
          setSelectedView('records');
        }, 100);
        return null;

      case 'stats':
        return (
          <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>📊 Статистика за 7 дней</Typography>
            <Grid container spacing={2}>
              {stats.map((stat) => (
                <Grid item xs={12} sm={6} md={4} key={stat.date}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>
                        {stat.date}
                      </Typography>
                      <Typography variant="h4">{stat.count} 🥚</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
            {stats.length === 0 && (
              <Typography color="text.secondary">Нет данных за указанный период</Typography>
            )}
          </Box>
        );

      case 'analytics':
        return (
          <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>📈 Аналитика</Typography>
            <Box sx={{ mb: 3 }}>
              <Typography gutterBottom>Период анализа: {analyticsDays} дней</Typography>
              <Slider
                value={analyticsDays}
                onChange={(e, val) => setAnalyticsDays(val)}
                valueLabelDisplay="auto"
                min={7}
                max={90}
                marks
              />
              <Button 
                variant="contained" 
                onClick={() => fetchAnalytics(analyticsDays)}
                sx={{ mt: 1 }}
              >
                Обновить
              </Button>
            </Box>
            
            {analytics ? (
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>Среднее в день</Typography>
                      <Typography variant="h4">{analytics.current_avg.toFixed(1)} 🥚</Typography>
                      <Typography color={analytics.trend >= 0 ? 'success.main' : 'error.main'}>
                        Тренд: {analytics.trend >= 0 ? '↑' : '↓'} {Math.abs(analytics.trend).toFixed(1)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>Максимум</Typography>
                      <Typography variant="h4">{analytics.max_day[1]} 🥚</Typography>
                      <Typography variant="caption">{analytics.max_day[0]}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>Минимум</Typography>
                      <Typography variant="h4">{analytics.min_day[1]} 🥚</Typography>
                      <Typography variant="caption">{analytics.min_day[0]}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="text.secondary" gutterBottom>Сравнение с прошлым периодом</Typography>
                      <Typography variant="h4" color={analytics.current_avg >= analytics.previous_avg ? 'success.main' : 'error.main'}>
                        {(analytics.current_avg - analytics.previous_avg).toFixed(1)}
                      </Typography>
                      <Typography variant="caption">Пред: {analytics.previous_avg.toFixed(1)}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            ) : (
              <Typography color="text.secondary">Недостаточно данных для анализа</Typography>
            )}
          </Box>
        );

      case 'plot':
        return (
          <Box>
            <Typography variant="h5" sx={{ mb: 3 }}>📈 График яйценоскости</Typography>
            <Box sx={{ mb: 3 }}>
              <Typography gutterBottom>Период: {plotDays} дней</Typography>
              <Slider
                value={plotDays}
                onChange={(e, val) => setPlotDays(val)}
                valueLabelDisplay="auto"
                min={7}
                max={180}
                marks
              />
              <Button 
                variant="contained" 
                onClick={() => fetchPlot(plotDays)}
                sx={{ mt: 1 }}
              >
                Обновить график
              </Button>
            </Box>
            {plotUrl ? (
              <Box component="img" src={plotUrl} alt="Egg production chart" sx={{ maxWidth: '100%' }} />
            ) : (
              <Typography color="text.secondary">Нет данных для построения графика</Typography>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* AppBar */}
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton edge="start" color="inherit" onClick={toggleDrawer} sx={{ mr: 2 }}>
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            🐔 Десять курочек
          </Typography>
          <Typography variant="body2" sx={{ mr: 2 }}>
            👋 {user?.username}
          </Typography>
          <IconButton color="inherit" onClick={logout}>
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Drawer
        variant="persistent"
        open={open}
        sx={{
          width: open ? drawerWidth : 60,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: open ? drawerWidth : 60,
            boxSizing: 'border-box',
            overflowX: 'hidden',
          },
        }}
      >
        <Toolbar>
          <IconButton onClick={toggleDrawer}>
            {open ? <ChevronLeftIcon /> : <MenuIcon />}
          </IconButton>
        </Toolbar>
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton onClick={() => setSelectedView(item.view)}>
                <ListItemIcon>{item.icon}</ListItemIcon>
                {open && <ListItemText primary={item.text} />}
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        
        {open && (
          <Box sx={{ p: 2, mt: 'auto' }}>
            <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
              <Typography variant="subtitle2" gutterBottom>📊 Общая статистика</Typography>
              <Typography variant="body2">Всего яиц: {summary.total_eggs} 🥚</Typography>
              <Typography variant="body2">Записей: {summary.records_count}</Typography>
              <Typography variant="body2">
                В среднем: {summary.avg_per_record.toFixed(1)}
              </Typography>
            </Paper>
            
            <Box sx={{ mt: 2, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                ❤️ Поддержать проект
              </Typography>
              <Button
                size="small"
                variant="outlined"
                href="https://pay.cloudtips.ru/p/dbed3f9a"
                target="_blank"
                sx={{ mt: 1 }}
                fullWidth
              >
                ☁️ CloudTips
              </Button>
            </Box>
          </Box>
        )}
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        <Container maxWidth="lg">
          {renderContent()}
        </Container>
      </Box>

      {/* Add Dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          📥 Добавить новую запись
          <IconButton onClick={() => setAddDialogOpen(false)} sx={{ position: 'absolute', right: 8, top: 8 }}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Дата"
            type="date"
            fullWidth
            value={newRecord.date}
            onChange={(e) => setNewRecord({ ...newRecord, date: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            margin="dense"
            label="Количество яиц"
            type="number"
            fullWidth
            value={newRecord.count}
            onChange={(e) => setNewRecord({ ...newRecord, count: parseInt(e.target.value) || 0 })}
            inputProps={{ min: 0 }}
          />
          <TextField
            margin="dense"
            label="Заметки"
            fullWidth
            value={newRecord.notes}
            onChange={(e) => setNewRecord({ ...newRecord, notes: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleAddRecord} variant="contained">Добавить</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          ✏️ Редактирование записи #{selectedRecord?.id}
          <IconButton onClick={() => setEditDialogOpen(false)} sx={{ position: 'absolute', right: 8, top: 8 }}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Дата"
            type="date"
            fullWidth
            value={editRecord.date}
            onChange={(e) => setEditRecord({ ...editRecord, date: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            margin="dense"
            label="Количество яиц"
            type="number"
            fullWidth
            value={editRecord.count}
            onChange={(e) => setEditRecord({ ...editRecord, count: parseInt(e.target.value) || 0 })}
            inputProps={{ min: 0 }}
          />
          <TextField
            margin="dense"
            label="Заметки"
            fullWidth
            value={editRecord.notes}
            onChange={(e) => setEditRecord({ ...editRecord, notes: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleUpdateRecord} variant="contained" startIcon={<SaveIcon />}>Сохранить</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>⚠️ Подтверждение удаления</DialogTitle>
        <DialogContent>
          <Typography>
            Вы уверены, что хотите удалить запись #{selectedRecord?.id} от {selectedRecord?.date}?
            Это действие нельзя отменить.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Отмена</Button>
          <Button onClick={handleDeleteRecord} variant="contained" color="error" startIcon={<DeleteIcon />}>
            Удалить
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Dashboard;
