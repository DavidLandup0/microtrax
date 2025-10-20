import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Chip,
  Alert,
  CircularProgress,
  Paper,
  Stack,
  FormControl,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
  ViewModule as ViewModuleIcon,
} from '@mui/icons-material';
import Plot from 'react-plotly.js';
import { Responsive, WidthProvider, Layout } from 'react-grid-layout';
import { ApiService } from '../services/api';
import { Experiment } from '../types';
import { useSettings } from '../contexts/SettingsContext';

const ResponsiveGridLayout = WidthProvider(Responsive);

interface MetricPlotsProps {
  experiments: Record<string, Experiment>;
  metrics: string[];
  selectedExperiments: string[];
  selectedMetrics: string[];
  onMetricToggle: (metric: string) => void;
}

const MetricPlots: React.FC<MetricPlotsProps> = ({
  experiments,
  metrics,
  selectedExperiments,
  selectedMetrics,
  onMetricToggle,
}) => {
  const [plots, setPlots] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [columns, setColumns] = useState(2);
  const [layouts, setLayouts] = useState<Layout[]>([]);
  const [containerWidth, setContainerWidth] = useState(1200);
  const { plotSettings, colorPalettes } = useSettings();

  // Apply smoothing + color palette
  const applySmoothingToData = (data: any[], smoothing: number) => {
    if (smoothing === 0) {
      return applyColorPalette(data);
    }

    const result: any[] = [];

    data.forEach((trace: any) => {
      if (!trace.x || !trace.y || trace.x.length < 3) {
        result.push(trace);
        return;
      }

      const originalTrace = {
        ...trace,
        opacity: 0.3,
        showlegend: false,
        hoverinfo: 'skip',
      };
      result.push(originalTrace);

      const maxWindow = Math.max(5, Math.floor(trace.y.length * 0.2));
      const windowSize = Math.max(1, Math.floor(smoothing * maxWindow));
      const smoothedY: number[] = [];

      for (let i = 0; i < trace.y.length; i++) {
        const start = Math.max(0, i - Math.floor(windowSize / 2));
        const end = Math.min(trace.y.length, i + Math.floor(windowSize / 2) + 1);

        let sum = 0;
        let count = 0;

        for (let j = start; j < end; j++) {
          if (trace.y[j] !== null && trace.y[j] !== undefined) {
            sum += trace.y[j];
            count++;
          }
        }

        smoothedY[i] = count > 0 ? sum / count : trace.y[i];
      }

      const smoothedTrace = {
        ...trace,
        y: smoothedY,
        name: trace.name ? `${trace.name} (smoothed)` : 'smoothed',
        line: {
          ...trace.line,
          width: (trace.line?.width || 2) + 1,
        },
      };
      result.push(smoothedTrace);
    });

    return applyColorPalette(result);
  };

  // Apply color palette
  const applyColorPalette = (data: any[]) => {
    const selectedPalette = colorPalettes.find(
      (p) => p.value === plotSettings.colorPalette
    );
    if (!selectedPalette) return data;

    return data.map((trace: any, index: number) => ({
      ...trace,
      line: {
        ...trace.line,
        color:
          selectedPalette.colors[index % selectedPalette.colors.length],
      },
    }));
  };

  // Track container width
  useEffect(() => {
    const updateWidth = () => {
      const availableWidth = window.innerWidth - 400;
      setContainerWidth(availableWidth);
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // Generate layout when metrics change
  useEffect(() => {
    const newLayouts = selectedMetrics.map((metric, index) => {
      const colWidth = Math.floor(12 / columns);
      const row = Math.floor(index / columns);
      const col = index % columns;

      return {
        i: metric,
        x: col * colWidth,
        y: row * 6,
        w: colWidth,
        h: 6,
        minH: 5,
        minW: colWidth,
        maxW: colWidth,
      };
    });
    setLayouts(newLayouts);
  }, [selectedMetrics, columns]);

  // Load plots when selections change or experiments data changes
  useEffect(() => {
    setPlots({});
    setErrors({});

    const loadPlots = async () => {
      if (selectedExperiments.length === 0 || selectedMetrics.length === 0) {
        setLoading({});
        return;
      }

      const loadingState: Record<string, boolean> = {};
      selectedMetrics.forEach((metric) => {
        loadingState[metric] = true;
      });
      setLoading(loadingState);

      const plotPromises = selectedMetrics.map(async (metric) => {
        try {
          const plotData = await ApiService.getPlot({
            experiments: selectedExperiments,
            metric,
            x_axis: plotSettings.xAxisMode,
            y_axis_scale: plotSettings.yAxisScale,
          });
          return { metric, data: plotData, error: null };
        } catch (error) {
          return { metric, data: null, error: `Failed to load ${metric}` };
        }
      });

      const results = await Promise.all(plotPromises);

      const newPlots: Record<string, any> = {};
      const newErrors: Record<string, string> = {};
      const newLoading: Record<string, boolean> = {};

      results.forEach(({ metric, data, error }) => {
        if (data) {
          newPlots[metric] = data;
        }
        if (error) {
          newErrors[metric] = error;
        }
        newLoading[metric] = false;
      });

      setPlots(newPlots);
      setErrors(newErrors);
      setLoading(newLoading);
    };

    loadPlots();
  }, [selectedExperiments, selectedMetrics, plotSettings, experiments]);

  if (selectedExperiments.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <TimelineIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Select Experiments
        </Typography>
        <Typography color="text.secondary">
          Choose one or more experiments from the sidebar to start visualizing
          metrics
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography
          variant="h6"
          sx={{ display: 'flex', alignItems: 'center', mb: 2 }}
        >
          <TrendingUpIcon sx={{ mr: 1 }} />
          Metrics ({selectedExperiments.length} experiments)
        </Typography>

        {/* Metric Selector */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Select metrics to visualize:
          </Typography>
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
            {metrics.map((metric) => (
              <Chip
                key={metric}
                label={metric}
                onClick={() => onMetricToggle(metric)}
                color={
                  selectedMetrics.includes(metric) ? 'primary' : 'default'
                }
                variant={
                  selectedMetrics.includes(metric) ? 'filled' : 'outlined'
                }
                clickable
                size="small"
              />
            ))}
          </Stack>
        </Box>

        {/* Layout Controls */}
        {selectedMetrics.length > 0 && (
          <Box
            sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 3 }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ViewModuleIcon fontSize="small" />
              <Typography variant="body2">Columns:</Typography>
              <FormControl size="small" sx={{ minWidth: 80 }}>
                <Select
                  value={columns}
                  onChange={(e) => setColumns(Number(e.target.value))}
                  sx={{ height: 32 }}
                >
                  <MenuItem value={1}>1</MenuItem>
                  <MenuItem value={2}>2</MenuItem>
                  <MenuItem value={3}>3</MenuItem>
                  <MenuItem value={4}>4</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </Box>
        )}
      </Box>

      {selectedMetrics.length === 0 && (
        <Alert severity="info">
          Select one or more metrics to display plots
        </Alert>
      )}

      {/* Plots Grid */}
      {selectedMetrics.length > 0 && (
        <ResponsiveGridLayout
          className="layout"
          layouts={{ lg: layouts }}
          breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
          cols={{ lg: 12, md: 12, sm: 12, xs: 12, xxs: 12 }}
          rowHeight={70}
          onLayoutChange={(layout: Layout[]) => setLayouts(layout)}
          isDraggable
          isResizable
          margin={[8, 8]}
          compactType="vertical"
          preventCollision
          autoSize
          useCSSTransforms
        >
          {selectedMetrics.map((metric) => (
            <div key={metric}>
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 2,
                  height: '100%',
                  ...(selectedMetrics.length === 1 && {
                    minHeight: 300,
                    minWidth: 400,
                  }),
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                {loading[metric] && (
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'center',
                      alignItems: 'center',
                      flex: 1,
                    }}
                  >
                    <CircularProgress />
                  </Box>
                )}

                {errors[metric] && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {errors[metric]}
                  </Alert>
                )}

                {plots[metric] && !loading[metric] && !errors[metric] && (
                  <Box
                    sx={{
                      flex: 1,
                      minHeight: 0,
                      width: '100%',
                      height: '100%',
                    }}
                  >
                    <Plot
                      key={`${metric}-${columns}-${containerWidth}-${plotSettings.smoothing}-${plotSettings.colorPalette}-${plotSettings.xAxisMode}`}
                      data={applySmoothingToData(
                        plots[metric].data || [],
                        plotSettings.smoothing
                      )}
                      layout={{
                        ...plots[metric].layout,
                        template: 'plotly_white',
                        autosize: true,
                        width: undefined,
                        height: undefined,
                        margin: { l: 50, r: 20, t: 40, b: 80 },
                        legend: {
                          orientation: 'h',
                          x: 0,
                          y: -0.2,
                          xanchor: 'left',
                          yanchor: 'top',
                          font: { size: 12 },
                        },
                      }}
                      config={{
                        responsive: true,
                        displayModeBar: true,
                        displaylogo: false,
                        modeBarButtonsToRemove: [
                          'pan2d',
                          'lasso2d',
                          'select2d',
                        ],
                      }}
                      style={{ width: '100%', height: '100%' }}
                      useResizeHandler
                    />
                  </Box>
                )}
              </Paper>
            </div>
          ))}
        </ResponsiveGridLayout>
      )}

      {selectedMetrics.length > 0 &&
        Object.keys(plots).length === 0 &&
        !Object.values(loading).some(Boolean) && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            No data available for the selected metrics and experiments
          </Alert>
        )}
    </Box>
  );
};

export default MetricPlots;
