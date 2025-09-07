import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardMedia,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Image as ImageIcon,
  Collections as CollectionsIcon,
} from '@mui/icons-material';
import { ApiService } from '../services/api';
import { Experiment, ImageData } from '../types';

interface ImageViewerProps {
  experiments: Record<string, Experiment>;
  selectedExperiments: string[];
}

const ImageViewer: React.FC<ImageViewerProps> = ({
  experiments,
  selectedExperiments,
}) => {
  const [selectedExperiment, setSelectedExperiment] = useState<string>('');
  const [images, setImages] = useState<ImageData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get experiments that have images
  const experimentsWithImages = selectedExperiments.filter(
    expId => experiments[expId]?.has_images
  );

  useEffect(() => {
    // Auto-select first experiment with images
    if (experimentsWithImages.length > 0 && !selectedExperiment) {
      setSelectedExperiment(experimentsWithImages[0]);
    }
  }, [experimentsWithImages, selectedExperiment]);

  useEffect(() => {
    const loadImages = async () => {
      if (!selectedExperiment) {
        setImages([]);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const imageData = await ApiService.getImages({ experiment: selectedExperiment });
        setImages(imageData);
      } catch (err) {
        setError('Failed to load images');
        console.error('Error loading images:', err);
      } finally {
        setLoading(false);
      }
    };

    loadImages();
  }, [selectedExperiment]);

  if (selectedExperiments.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <CollectionsIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Select Experiments
        </Typography>
        <Typography color="text.secondary">
          Choose experiments from the sidebar to view their images
        </Typography>
      </Box>
    );
  }

  if (experimentsWithImages.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <ImageIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No Images Found
        </Typography>
        <Typography color="text.secondary">
          The selected experiments don't contain any logged images
        </Typography>
      </Box>
    );
  }

  const groupedImages = images.reduce((acc, image) => {
    if (!acc[image.step]) {
      acc[image.step] = [];
    }
    acc[image.step].push(image);
    return acc;
  }, {} as Record<number, ImageData[]>);

  const sortedSteps = Object.keys(groupedImages).sort((a, b) => Number(a) - Number(b));

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <ImageIcon sx={{ mr: 1 }} />
          Images
        </Typography>

        {/* Experiment Selector */}
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Select Experiment</InputLabel>
          <Select
            value={selectedExperiment}
            onChange={(e) => setSelectedExperiment(e.target.value)}
            label="Select Experiment"
          >
            {experimentsWithImages.map((expId) => {
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

      {!loading && images.length === 0 && selectedExperiment && (
        <Alert severity="info">
          No images found in this experiment
        </Alert>
      )}

      {/* Images Grid */}
      {!loading && images.length > 0 && (
        <Box>
          {sortedSteps.map((step) => (
            <Box key={step} sx={{ mb: 4 }}>
              <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="h6">Step {step}</Typography>
                <Chip 
                  label={`${groupedImages[Number(step)].length} images`} 
                  size="small" 
                  variant="outlined"
                />
              </Box>
              
              <Grid container spacing={2}>
                {groupedImages[Number(step)].map((image, index) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={`${step}-${index}`}>
                    <Card 
                      elevation={0} 
                      sx={{ 
                        border: 1, 
                        borderColor: 'divider',
                        '&:hover': {
                          boxShadow: 2,
                        }
                      }}
                    >
                      <CardMedia
                        component="img"
                        image={`data:image/png;base64,${image.data}`}
                        alt={`${image.key} at step ${step}`}
                        sx={{
                          height: 200,
                          objectFit: 'contain',
                          bgcolor: 'grey.50',
                        }}
                      />
                      <CardContent sx={{ p: 2 }}>
                        <Typography variant="body2" fontWeight={500} noWrap>
                          {image.key}
                        </Typography>
                        {image.label && (
                          <Typography variant="caption" color="text.secondary" display="block">
                            Label: {image.label}
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
};

export default ImageViewer;