import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface PlotSettings {
  smoothing: number;
  colorPalette: string;
  plotStyle: string;
  autoRefreshEnabled: boolean;
  autoRefreshInterval: number; // in seconds
}

export interface ColorPalette {
  value: string;
  label: string;
  colors: string[];
}

interface SettingsContextType {
  plotSettings: PlotSettings;
  updatePlotSettings: (settings: Partial<PlotSettings>) => void;
  colorPalettes: ColorPalette[];
  setColorPalettes: (palettes: ColorPalette[]) => void;
}

const defaultPlotSettings: PlotSettings = {
  smoothing: 0,
  colorPalette: 'plotly',
  plotStyle: 'none',
  autoRefreshEnabled: true,
  autoRefreshInterval: 5, // 5 seconds
};

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

interface SettingsProviderProps {
  children: ReactNode;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [plotSettings, setPlotSettings] = useState<PlotSettings>(defaultPlotSettings);
  const [colorPalettes, setColorPalettes] = useState<ColorPalette[]>([]);

  const updatePlotSettings = (newSettings: Partial<PlotSettings>) => {
    setPlotSettings(prev => ({ ...prev, ...newSettings }));
  };

  return (
    <SettingsContext.Provider value={{ plotSettings, updatePlotSettings, colorPalettes, setColorPalettes }}>
      {children}
    </SettingsContext.Provider>
  );
};