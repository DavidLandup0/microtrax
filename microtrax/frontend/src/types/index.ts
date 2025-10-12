export interface Experiment {
  id: string;
  metadata: {
    experiment_id: string;
    start_time: number;
    start_time_iso: string;
    status: 'running' | 'completed' | 'interrupted' | 'recovered';
    end_time?: number;
    total_steps?: number;
    track_resources?: boolean;
  };
  log_count: number;
  has_resources: boolean;
  has_images: boolean;
  has_text: boolean;
}

export interface ExperimentsResponse {
  experiments: Record<string, Experiment>;
  metrics: string[];
}

export interface PlotRequest {
  experiments: string[];
  metric: string;
  x_axis?: 'step' | 'time';
}

export interface ImagesRequest {
  experiment: string;
}

export interface ImageData {
  step: number;
  key: string;
  data: string; // base64
  label?: string;
}

export interface TextRequest {
  experiment: string;
}

export interface TextEntry {
  type: 'text';
  step: number;
  timestamp: number;
  columns: string[];
  rows: Record<string, any>[];
}