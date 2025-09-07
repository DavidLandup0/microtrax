from fastapi import APIRouter, HTTPException, Request
import json
from pathlib import Path

from microtrax.backend.services.experiment_service import load_experiments, extract_metrics
from microtrax.backend.domain.schemas import RenameExperimentRequest, DeleteExperimentRequest
from microtrax.constants import EXPERIMENTS_DIR, RESOURCES_DIR

router = APIRouter(prefix="/api", tags=["experiments"])

@router.get("/experiments")
async def get_experiments(request: Request):
    """Get all experiments and available metrics"""
    logdir = request.app.state.logdir

    try:
        experiments = load_experiments(logdir)
        metrics = extract_metrics(experiments)

        # Simplify experiment data for frontend
        trimmed_experiments = {}
        for exp_id, exp_data in experiments.items():
            trimmed_experiments[exp_id] = {
                'id': exp_id,
                'metadata': exp_data['metadata'],
                'log_count': len(exp_data['logs']),
                'has_resources': len(exp_data.get('resources', [])) > 0,
                'has_images': exp_data['metadata'].get('has_images', False)
            }

        return {
            'experiments': trimmed_experiments,
            'metrics': metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/experiments/{experiment_id}/rename")
async def rename_experiment(experiment_id: str, request: Request, rename_request: RenameExperimentRequest):
    """Rename an experiment"""
    logdir = request.app.state.logdir
    experiments_dir = Path(logdir) / EXPERIMENTS_DIR
    experiment_file = experiments_dir / f'{experiment_id}.jsonl'

    if not experiment_file.exists():
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        # Read the experiment file
        lines = []
        with open(experiment_file, 'r') as f:
            lines = f.readlines()

        # Update the metadata entry
        updated_lines = []
        for line in lines:
            try:
                entry = json.loads(line.strip())
                if entry.get('type') == 'metadata':
                    entry['name'] = rename_request.name
                updated_lines.append(json.dumps(entry) + '\n')
            except json.JSONDecodeError:
                updated_lines.append(line)

        # Write back the updated file
        with open(experiment_file, 'w') as f:
            f.writelines(updated_lines)

        return {"success": True, "message": f"Experiment renamed to '{rename_request.name}'"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename experiment: {str(e)}")


@router.delete("/experiments/{experiment_id}")
async def delete_experiment(experiment_id: str, request: Request, delete_request: DeleteExperimentRequest):
    """Delete an experiment"""
    if not delete_request.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required to delete experiment")

    logdir = request.app.state.logdir
    experiments_dir = Path(logdir) / EXPERIMENTS_DIR
    resources_dir = Path(logdir) / RESOURCES_DIR

    experiment_file = experiments_dir / f'{experiment_id}.jsonl'
    resource_file = resources_dir / f'{experiment_id}_resources.jsonl'

    if not experiment_file.exists():
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        # Delete experiment log file
        experiment_file.unlink()

        # Delete resource file if it exists
        if resource_file.exists():
            resource_file.unlink()

        return {"success": True, "message": "Experiment deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete experiment: {str(e)}")
