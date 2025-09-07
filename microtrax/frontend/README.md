# microtrax React Frontend

Modern React dashboard for microtrax experiment tracking.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## Features

- 🧪 **Experiment Management**: Select and compare multiple experiments
- 📊 **Interactive Metrics**: Real-time Plotly.js charts with zoom, pan, hover
- 🖼️ **Image Visualization**: View logged images with labels and metadata
- 🎨 **Modern UI**: Clean Material-UI design with responsive layout
- ⚡ **Live Updates**: Auto-refresh for running experiments
- 🔍 **Smart Filtering**: Filter experiments by status, date, and content

## Architecture

- **React 18** with TypeScript
- **Material-UI** for components and theming
- **Plotly.js** for interactive visualizations
- **Axios** for API communication
- **date-fns** for date formatting

## Backend Integration

The frontend communicates with the FastAPI backend running on `http://localhost:8080` by default.

Make sure to start the backend first:
```bash
mtx serve -f ./your_experiments_dir
```