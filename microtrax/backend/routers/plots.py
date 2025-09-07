from fastapi import APIRouter, HTTPException, Request
import plotly.colors
import plotly.io

from microtrax.backend.services.experiment_service import load_experiments
from microtrax.backend.services.plot_service import create_metric_plot
from microtrax.backend.domain.schemas import PlotRequest

router = APIRouter(prefix="/api", tags=["plots"])


@router.get("/plot-options")
async def get_plot_options():
    """Get available color scales and templates from Plotly"""
    try:
        # Dynamically get all qualitative color scales
        color_scales = []
        qualitative_palettes = {
            name: getattr(plotly.colors.qualitative, name)
            for name in dir(plotly.colors.qualitative)
            if not name.startswith("_")
        }

        for name, colors in qualitative_palettes.items():
            color_scales.append({
                "value": name.lower(),
                "label": name,
                "colors": colors,
                "type": "qualitative"
            })

        # Get available templates
        templates = [{"value": name, "label": name} for name in plotly.io.templates]

        return {
            "color_scales": color_scales,
            "templates": templates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plot")
async def create_plot(request: Request, plot_request: PlotRequest):
    """Create a plot for a specific metric"""
    logdir = request.app.state.logdir

    try:
        experiments = load_experiments(logdir)
        plot_data = create_metric_plot(experiments, plot_request.experiments, plot_request.metric)
        return plot_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
