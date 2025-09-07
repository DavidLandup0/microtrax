import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Divider,
  Drawer,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
} from '@mui/icons-material';
import { useSettings } from '../contexts/SettingsContext';
import { ApiService } from '../services/api';

interface SettingsSidePanelProps {
  open: boolean;
  onClose: () => void;
}

const SettingsSidePanel: React.FC<SettingsSidePanelProps> = ({ open, onClose }) => {
  const { plotSettings, updatePlotSettings, setColorPalettes } = useSettings();
  const [collapsed, setCollapsed] = useState(false);
  const [localColorPalettes, setLocalColorPalettes] = useState<Array<{value: string, label: string, colors: string[]}>>([]);
  const [plotTemplates, setPlotTemplates] = useState<Array<{value: string, label: string}>>([]);

  useEffect(() => {
    const loadPlotOptions = async () => {
      try {
        const options = await ApiService.getPlotOptions();
        const palettes = options.color_scales.map(scale => ({
          value: scale.value,
          label: scale.label,
          colors: scale.colors
        }));
        setLocalColorPalettes(palettes);
        setColorPalettes(palettes);
        setPlotTemplates([
          { value: 'none', label: 'None (Default)' },
          ...options.templates
        ]);
      } catch (error) {
        console.warn('Failed to load plot options, using fallbacks:', error);
        // Fallback values
        const fallbackPalettes = [
          { value: 'plotly', label: 'Plotly', colors: ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A'] }
        ];
        setLocalColorPalettes(fallbackPalettes);
        setColorPalettes(fallbackPalettes);
      }
    };

    loadPlotOptions();
  }, []);

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      variant="persistent"
      sx={{
        width: collapsed ? 60 : 320,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: collapsed ? 60 : 320,
          boxSizing: 'border-box',
          backgroundColor: 'background.paper',
          borderLeft: 1,
          borderColor: 'divider',
          top: 64, // Below header
          height: 'calc(100vh - 64px)',
          zIndex: 1200,
        },
      }}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Header */}
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          p: 2, 
          borderBottom: 1, 
          borderColor: 'divider',
          justifyContent: collapsed ? 'center' : 'space-between'
        }}>
          {!collapsed && (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <SettingsIcon sx={{ mr: 1 }} />
              <Typography variant="h6">Plot Settings</Typography>
            </Box>
          )}
          <IconButton 
            onClick={() => setCollapsed(!collapsed)}
            size="small"
          >
            {collapsed ? <ChevronLeftIcon /> : <ChevronRightIcon />}
          </IconButton>
        </Box>

        {/* Settings Content */}
        <Collapse in={!collapsed} timeout={300}>
          <Box sx={{ p: 2, overflowY: 'auto', flex: 1 }}>
            {/* Smoothing Slider */}
            <Paper sx={{ p: 2, mb: 2 }} elevation={1}>
              <Typography variant="subtitle1" gutterBottom>
                Line Smoothing
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Apply smoothing to plot lines (0 = raw data, 1 = maximum smoothing)
              </Typography>
              <Slider
                value={plotSettings.smoothing}
                onChange={(_, value) => updatePlotSettings({ smoothing: value as number })}
                min={0}
                max={1}
                step={0.05}
                valueLabelDisplay="on"
                marks={[
                  { value: 0, label: '0' },
                  { value: 0.5, label: '0.5' },
                  { value: 1, label: '1' },
                ]}
                sx={{ mt: 1 }}
              />
            </Paper>

            {/* Color Palette */}
            <Paper sx={{ p: 2, mb: 2 }} elevation={1}>
              <Typography variant="subtitle1" gutterBottom>
                Color Palette
              </Typography>
              <FormControl fullWidth size="small">
                <InputLabel>Palette</InputLabel>
                <Select
                  value={plotSettings.colorPalette}
                  label="Palette"
                  onChange={(e) => updatePlotSettings({ colorPalette: e.target.value })}
                  MenuProps={{
                    PaperProps: {
                      style: {
                        maxHeight: 200,
                      },
                    },
                  }}
                >
                  {localColorPalettes.map((palette) => (
                    <MenuItem key={palette.value} value={palette.value}>
                      {palette.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Paper>
          </Box>
        </Collapse>
      </Box>
    </Drawer>
  );
};

export default SettingsSidePanel;