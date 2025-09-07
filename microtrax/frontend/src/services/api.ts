import axios from 'axios';
import { ExperimentsResponse, PlotRequest, ImagesRequest, ImageData } from '../types';

const API_BASE = process.env.NODE_ENV === 'development' ? 'http://localhost:8080' : '';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export class ApiService {
  static async getExperiments(): Promise<ExperimentsResponse> {
    const response = await api.get('/api/experiments');
    return response.data;
  }

  static async getPlot(request: PlotRequest): Promise<any> {
    const response = await api.post('/api/plot', request);
    return response.data;
  }

  static async getImages(request: ImagesRequest): Promise<ImageData[]> {
    const response = await api.post('/api/images', request);
    return response.data;
  }

  static async renameExperiment(experimentId: string, name: string): Promise<void> {
    await api.put(`/api/experiments/${experimentId}/rename`, { name });
  }

  static async deleteExperiment(experimentId: string): Promise<void> {
    await api.delete(`/api/experiments/${experimentId}`, { 
      data: { confirm: true }
    });
  }

  static async getPlotOptions(): Promise<{color_scales: Array<{value: string, label: string, colors: string[], type: string}>, templates: Array<{value: string, label: string}>}> {
    const response = await api.get('/api/plot-options');
    return response.data;
  }
}