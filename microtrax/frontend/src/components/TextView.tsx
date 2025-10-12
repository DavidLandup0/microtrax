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
  const [textData, setTextData] = useState<TextEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedStep, setSelectedStep] = useState<number | 'all'>('all');

  useEffect(() => {
    const loadTextData = async () => {
      if (selectedExperiments.length === 0) {
        setTextData([]);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        // For now, load text from the first selected experiment
        // TODO: Support multiple experiments
        const experimentId = selectedExperiments[0];
        const data = await ApiService.getText({ experiment: experimentId });
        setTextData(data);
      } catch (err) {
        setError('Failed to load text data');
        console.error('Error loading text:', err);
      } finally {
        setLoading(false);
      }
    };

    loadTextData();
  }, [selectedExperiments, experiments]);

  if (selectedExperiments.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <TableChartIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Select an Experiment
        </Typography>
        <Typography color="text.secondary">
          Choose an experiment from the sidebar to view logged text
        </Typography>
      </Box>
    );
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (textData.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <TableChartIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No Text Logged
        </Typography>
        <Typography color="text.secondary">
          Use mtx.log_text() to log text data
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
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
          <TableChartIcon sx={{ mr: 1 }} />
          Text Data ({allRows.length} rows)
        </Typography>

        {steps.length > 1 && (
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <Select
              value={selectedStep}
              onChange={(e) => setSelectedStep(e.target.value as number | 'all')}
            >
              <MenuItem value="all">All Steps</MenuItem>
              {steps.map(step => (
                <MenuItem key={step} value={step}>Step {step}</MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </Box>

      {/* Table */}
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
    </Box>
  );
};

export default TextView;
