import React, { useState } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Typography,
  Chip,
  Skeleton,
  alpha,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Alert,
} from '@mui/material';
import {
  PlayArrow as RunningIcon,
  CheckCircle as CompletedIcon,
  Error as InterruptedIcon,
  Refresh as RecoveredIcon,
  Image as ImageIcon,
  Monitor as ResourceIcon,
  TableChart as TextIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { Experiment } from '../types';

interface ExperimentListProps {
  experiments: Record<string, Experiment>;
  selectedExperiments: string[];
  onExperimentToggle: (experimentId: string) => void;
  onExperimentRename: (experimentId: string, newName: string) => Promise<void>;
  onExperimentDelete: (experimentId: string) => Promise<void>;
  loading: boolean;
}

const ExperimentList: React.FC<ExperimentListProps> = ({
  experiments,
  selectedExperiments,
  onExperimentToggle,
  onExperimentRename,
  onExperimentDelete,
  loading,
}) => {
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedExperiment, setSelectedExperiment] = useState<string | null>(null);
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [renameName, setRenameName] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <RunningIcon sx={{ color: 'success.main' }} />;
      case 'completed':
        return <CompletedIcon sx={{ color: 'primary.main' }} />;
      case 'interrupted':
        return <InterruptedIcon sx={{ color: 'error.main' }} />;
      case 'recovered':
        return <RecoveredIcon sx={{ color: 'warning.main' }} />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'completed':
        return 'primary';
      case 'interrupted':
        return 'error';
      case 'recovered':
        return 'warning';
      default:
        return 'default';
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, experimentId: string) => {
    event.stopPropagation();
    setMenuAnchor(event.currentTarget);
    setSelectedExperiment(experimentId);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedExperiment(null);
  };

  const handleRenameClick = () => {
    if (selectedExperiment && experiments[selectedExperiment]) {
      const currentName = (experiments[selectedExperiment].metadata as any).name || '';
      setRenameName(currentName);
      setRenameDialogOpen(true);
      setMenuAnchor(null); // Close menu but keep selectedExperiment
    }
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
    setMenuAnchor(null); // Close menu but keep selectedExperiment
  };

  const handleRename = async () => {
    if (selectedExperiment && renameName.trim()) {
      try {
        setActionLoading(true);
        setError(null);
        console.log('Renaming experiment:', selectedExperiment, 'to:', renameName.trim());
        await onExperimentRename(selectedExperiment, renameName.trim());
        console.log('Rename completed successfully');
        setRenameDialogOpen(false);
        setRenameName('');
        setSelectedExperiment(null);
      } catch (err) {
        console.error('Rename error:', err);
        setError(err instanceof Error ? err.message : 'Failed to rename experiment');
      } finally {
        setActionLoading(false);
      }
    } else {
      console.log('Rename conditions not met:', { selectedExperiment, renameName: renameName.trim() });
    }
  };

  const handleDelete = async () => {
    console.log('handleDelete called, selectedExperiment:', selectedExperiment);
    if (selectedExperiment) {
      try {
        setActionLoading(true);
        setError(null);
        console.log('Calling onExperimentDelete with:', selectedExperiment);
        await onExperimentDelete(selectedExperiment);
        console.log('Delete successful');
        setDeleteDialogOpen(false);
        setSelectedExperiment(null);
      } catch (err) {
        console.error('Delete error:', err);
        setError(err instanceof Error ? err.message : 'Failed to delete experiment');
      } finally {
        setActionLoading(false);
      }
    } else {
      console.log('No selectedExperiment, cannot delete');
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 2 }}>
        {[...Array(3)].map((_, i) => (
          <Box key={i} sx={{ mb: 2 }}>
            <Skeleton variant="rectangular" width="100%" height={80} sx={{ borderRadius: 1 }} />
          </Box>
        ))}
      </Box>
    );
  }

  const experimentsList = Object.values(experiments).sort(
    (a, b) => new Date(b.metadata.start_time_iso).getTime() - new Date(a.metadata.start_time_iso).getTime()
  );

  if (experimentsList.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="text.secondary">
          No experiments found. Start logging with microtrax!
        </Typography>
      </Box>
    );
  }

  return (
    <>
      <List sx={{ p: 0, maxHeight: 'calc(100vh - 280px)', overflow: 'auto' }}>
        {experimentsList.map((experiment) => {
        const isSelected = selectedExperiments.includes(experiment.id);
        const startTime = new Date(experiment.metadata.start_time_iso);
        const displayName = (experiment.metadata as any).name || experiment.id;

          return (
            <ListItem key={experiment.id} disablePadding>
            <ListItemButton
              onClick={() => onExperimentToggle(experiment.id)}
              sx={{
                borderRadius: 1,
                mb: 0.5,
                mx: 1,
                bgcolor: isSelected ? alpha('#3b82f6', 0.1) : 'transparent',
                '&:hover': {
                  bgcolor: isSelected ? alpha('#3b82f6', 0.15) : alpha('#000', 0.04),
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                <Checkbox
                  checked={isSelected}
                  size="small"
                  sx={{ p: 0 }}
                />
              </ListItemIcon>

              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                    {getStatusIcon(experiment.metadata.status)}
                    <Typography
                      variant="body2"
                      sx={{ ml: 0.5, fontWeight: 500, fontSize: '0.875rem' }}
                      noWrap
                    >
                      {displayName}
                    </Typography>
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      {format(startTime, 'MMM dd, HH:mm')}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
                      <Chip
                        label={experiment.metadata.status}
                        size="small"
                        color={getStatusColor(experiment.metadata.status) as any}
                        variant="outlined"
                        sx={{ fontSize: '0.65rem', height: 18 }}
                      />
                      
                      {experiment.log_count > 0 && (
                        <Chip
                          label={`${experiment.log_count} logs`}
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.65rem', height: 18 }}
                        />
                      )}
                      
                      {experiment.has_images && (
                        <Chip
                          icon={<ImageIcon sx={{ fontSize: 10 }} />}
                          label="images"
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.65rem', height: 18 }}
                        />
                      )}
                      
                      {experiment.has_resources && (
                        <Chip
                          icon={<ResourceIcon sx={{ fontSize: 10 }} />}
                          label="resources"
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.65rem', height: 18 }}
                        />
                      )}

                      {experiment.has_text && (
                        <Chip
                          icon={<TextIcon sx={{ fontSize: 10 }} />}
                          label="text"
                          size="small"
                          variant="outlined"
                          sx={{ fontSize: '0.65rem', height: 18 }}
                        />
                      )}
                    </Box>
                  </Box>
                }
              />
              
              <IconButton
                size="small"
                onClick={(e) => handleMenuOpen(e, experiment.id)}
                sx={{ ml: 1 }}
              >
                <MoreVertIcon fontSize="small" />
              </IconButton>
            </ListItemButton>
            </ListItem>
          );
        })}
      </List>

    {/* Context Menu */}
    <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={handleRenameClick}>
          <EditIcon sx={{ mr: 1, fontSize: 16 }} />
          Rename
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1, fontSize: 16 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Rename Dialog */}
      <Dialog open={renameDialogOpen} onClose={() => !actionLoading && setRenameDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Rename Experiment</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            autoFocus
            margin="dense"
            label="Experiment Name"
            fullWidth
            variant="outlined"
            value={renameName}
            onChange={(e) => setRenameName(e.target.value)}
            disabled={actionLoading}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRenameDialogOpen(false)} disabled={actionLoading}>
            Cancel
          </Button>
          <Button onClick={handleRename} disabled={actionLoading || !renameName.trim()}>
            Rename
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => !actionLoading && setDeleteDialogOpen(false)} maxWidth="sm">
        <DialogTitle>Delete Experiment</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Typography>
            Are you sure you want to delete this experiment? This action cannot be undone.
          </Typography>
          {selectedExperiment && experiments[selectedExperiment] && (
            <Typography variant="body2" sx={{ mt: 1, fontWeight: 500 }}>
              {(experiments[selectedExperiment].metadata as any).name || experiments[selectedExperiment].id}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={actionLoading}>
            Cancel
          </Button>
          <Button onClick={handleDelete} color="error" disabled={actionLoading}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ExperimentList;