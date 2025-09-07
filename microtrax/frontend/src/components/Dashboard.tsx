import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  AppBar,
  Toolbar,
  Chip,
  IconButton,
  Alert,
} from '@mui/material';
import {
  Science as ScienceIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  Image as ImageIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import ExperimentList from './ExperimentList';
import MetricPlots from './MetricPlots';
import ImageViewer from './ImageViewer';
import SettingsSidePanel from './SettingsSidePanel';
import { ApiService } from '../services/api';
import { Experiment } from '../types';

const Dashboard: React.FC = () => {
  const [experiments, setExperiments] = useState<Record<string, Experiment>>({});
  const [metrics, setMetrics] = useState<string[]>([]);
  const [selectedExperiments, setSelectedExperiments] = useState<string[]>([]);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<'plots' | 'images'>('plots');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ApiService.getExperiments();
      setExperiments(data.experiments);
      setMetrics(data.metrics);
    } catch (err) {
      setError('Failed to load experiments. Make sure the microtrax server is running via `mtx serve`.');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Auto-refresh every 30 seconds for live experiments
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleExperimentToggle = (experimentId: string) => {
    setSelectedExperiments(prev => 
      prev.includes(experimentId)
        ? prev.filter(id => id !== experimentId)
        : [...prev, experimentId]
    );
  };

  const handleMetricToggle = (metric: string) => {
    setSelectedMetrics(prev =>
      prev.includes(metric)
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    );
  };

  const handleExperimentRename = async (experimentId: string, newName: string) => {
    await ApiService.renameExperiment(experimentId, newName);
    // Update local state instead of reloading
    setExperiments(prev => ({
      ...prev,
      [experimentId]: {
        ...prev[experimentId],
        metadata: {
          ...prev[experimentId].metadata,
          name: newName
        }
      }
    }));
  };

  const handleExperimentDelete = async (experimentId: string) => {
    await ApiService.deleteExperiment(experimentId);
    // Remove from selected experiments if it was selected
    setSelectedExperiments(prev => prev.filter(id => id !== experimentId));
    // Reload data to reflect the change
    await loadData();
  };

  const experimentCount = Object.keys(experiments).length;
  const runningCount = Object.values(experiments).filter(
    exp => exp.metadata.status === 'running'
  ).length;
  const hasImages = Object.values(experiments).some(exp => exp.has_images);

  return (
    <Box sx={{ flexGrow: 1, transform: 'scale(0.9)', transformOrigin: 'top left', width: '111.11%', height: '111.11%' }}>
      {/* Header */}
      <AppBar position="static" elevation={0} sx={{ bgcolor: 'white', color: 'text.primary', borderBottom: 1, borderColor: 'divider' }}>
        <Toolbar>
          <ScienceIcon sx={{ mr: 2, color: 'primary.main' }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: 'text.primary', fontWeight: 600 }}>
            microtrax Dashboard
          </Typography>
          <Chip 
            label={`${experimentCount} experiments`} 
            size="small" 
            sx={{ mr: 1 }} 
          />
          {runningCount > 0 && (
            <Chip 
              label={`${runningCount} running`} 
              size="small" 
              color="success" 
              sx={{ mr: 2 }} 
            />
          )}
          <IconButton onClick={loadData} disabled={loading}>
            <RefreshIcon />
          </IconButton>
          <IconButton onClick={() => setSettingsOpen(!settingsOpen)}>
            <SettingsIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container 
        maxWidth="xl" 
        sx={{ 
          mt: 3, 
          mb: 3,
          maxWidth: settingsOpen ? 'calc(100% - 340px)' : '100%',
          transition: 'max-width 0.3s ease-in-out',
        }}
      >
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Sidebar - Experiment List */}
          <Grid item xs={12} lg={3}>
            <Card sx={{ height: 'calc(100vh - 200px)', overflow: 'hidden' }}>
              <CardContent sx={{ p: 0 }}>
                <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                    <ScienceIcon sx={{ mr: 1, fontSize: 20 }} />
                    Experiments
                  </Typography>
                </Box>
                <ExperimentList
                  experiments={experiments}
                  selectedExperiments={selectedExperiments}
                  onExperimentToggle={handleExperimentToggle}
                  onExperimentRename={handleExperimentRename}
                  onExperimentDelete={handleExperimentDelete}
                  loading={loading}
                />
              </CardContent>
            </Card>
          </Grid>

          {/* Main Content */}
          <Grid item xs={12} lg={9}>
            {/* Tab Navigation */}
            <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
              <Chip
                icon={<TimelineIcon />}
                label="Metrics"
                onClick={() => setActiveTab('plots')}
                color={activeTab === 'plots' ? 'primary' : 'default'}
                variant={activeTab === 'plots' ? 'filled' : 'outlined'}
                clickable
              />
              {hasImages && (
                <Chip
                  icon={<ImageIcon />}
                  label="Images"
                  onClick={() => setActiveTab('images')}
                  color={activeTab === 'images' ? 'primary' : 'default'}
                  variant={activeTab === 'images' ? 'filled' : 'outlined'}
                  clickable
                />
              )}
            </Box>

            {/* Content Area */}
            <Card sx={{ minHeight: 'calc(100vh - 250px)' }}>
              <CardContent>
                {activeTab === 'plots' && (
                  <MetricPlots
                    experiments={experiments}
                    metrics={metrics}
                    selectedExperiments={selectedExperiments}
                    selectedMetrics={selectedMetrics}
                    onMetricToggle={handleMetricToggle}
                  />
                )}
                {activeTab === 'images' && (
                  <ImageViewer
                    experiments={experiments}
                    selectedExperiments={selectedExperiments}
                  />
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>

      {/* Settings Side Panel */}
      <SettingsSidePanel 
        open={settingsOpen} 
        onClose={() => setSettingsOpen(false)} 
      />
    </Box>
  );
};

export default Dashboard;