import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  TableChart as TableChartIcon,
} from '@mui/icons-material';
import { ApiService } from '../services/api';
import { Experiment, TextEntry } from '../types';

interface TextViewProps {
  experiments: Record<string, Experiment>;
  selectedExperiments: string[];
}

const TextView: React.FC<TextViewProps> = ({ experiments, selectedExperiments }) => {
  const [selectedExperiment, setSelectedExperiment] = useState<string>('');
  const [textData, setTextData] = useState<TextEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedStep, setSelectedStep] = useState<number | 'all'>('all');

  // Get experiments that have text
  const experimentsWithText = selectedExperiments.filter(
    expId => experiments[expId]?.has_text
  );

  useEffect(() => {
    // Auto-select first experiment with text
    if (experimentsWithText.length > 0 && !selectedExperiment) {
      setSelectedExperiment(experimentsWithText[0]);
    }
  }, [experimentsWithText, selectedExperiment]);

  useEffect(() => {
    const loadTextData = async () => {
      if (!selectedExperiment) {
        setTextData([]);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const data = await ApiService.getText({ experiment: selectedExperiment });
        setTextData(data);
      } catch (err) {
        setError('Failed to load text data');
        console.error('Error loading text:', err);
      } finally {
        setLoading(false);
      }
    };

    loadTextData();
  }, [selectedExperiment]);

  if (selectedExperiments.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <TableChartIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Select Experiments
        </Typography>
        <Typography color="text.secondary">
          Choose experiments from the sidebar to view their text data
        </Typography>
      </Box>
    );
  }

  if (experimentsWithText.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <TableChartIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No Text Found
        </Typography>
        <Typography color="text.secondary">
          The selected experiments don't contain any logged text
        </Typography>
      </Box>
    );
  }

  // Get unique steps
  const steps = Array.from(new Set(textData.map(entry => entry.step))).sort((a, b) => a - b);

  // Filter data by selected step
  const filteredData = selectedStep === 'all'
    ? textData
    : textData.filter(entry => entry.step === selectedStep);

  // Collect all unique columns across all filtered entries
  const allColumns = Array.from(
    new Set(filteredData.flatMap(entry => entry.columns))
  );

  // Flatten all rows from all entries
  const allRows: Array<Record<string, any>> = filteredData.flatMap(entry =>
    entry.rows.map(row => ({ ...row, step: entry.step, timestamp: entry.timestamp }))
  );

  const truncateText = (text: string, maxLength: number = 100) => {
    if (typeof text !== 'string') return String(text);
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TableChartIcon sx={{ mr: 1 }} />
          Text Data
        </Typography>

        {/* Experiment Selector */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Select Experiment</InputLabel>
            <Select
              value={selectedExperiment}
              onChange={(e) => setSelectedExperiment(e.target.value)}
              label="Select Experiment"
            >
              {experimentsWithText.map((expId) => {
                const exp = experiments[expId];
                const displayName = expId.split('_').slice(-1)[0];
                return (
                  <MenuItem key={expId} value={expId}>
                    {displayName} ({exp.metadata.status})
                  </MenuItem>
                );
              })}
            </Select>
          </FormControl>

          {steps.length > 1 && (
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Filter by Step</InputLabel>
              <Select
                value={selectedStep}
                onChange={(e) => setSelectedStep(e.target.value as number | 'all')}
                label="Filter by Step"
              >
                <MenuItem value="all">All Steps</MenuItem>
                {steps.map(step => (
                  <MenuItem key={step} value={step}>Step {step}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {!loading && textData.length === 0 && selectedExperiment && (
        <Alert severity="info">
          No text data found in this experiment
        </Alert>
      )}

      {/* Table */}
      {!loading && textData.length > 0 && (
        <TableContainer component={Paper} elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 'bold', bgcolor: 'grey.100' }}>Step</TableCell>
                {allColumns.map(column => (
                  <TableCell key={column} sx={{ fontWeight: 'bold', bgcolor: 'grey.100' }}>
                    {column}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {allRows.map((row, index) => (
                <TableRow key={index} hover>
                  <TableCell>{row.step}</TableCell>
                  {allColumns.map(column => (
                    <TableCell
                      key={column}
                      title={row[column]} // Full text on hover
                      sx={{ maxWidth: 300 }}
                    >
                      {truncateText(row[column] || '')}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default TextView;
