from typing import Dict, List, Any
import plotly.graph_objects as go
from microtrax.constants import RESOURCE_METRICS


def create_metric_plot(experiments: Dict[str, Dict[str, Any]], selected_experiments: List[str], metric: str) -> Dict:
    """Create a Plotly figure for a specific metric"""
    fig = go.Figure()

    # Check if this is a resource metric

    for exp_id in selected_experiments:
        if exp_id not in experiments:
            continue

        exp_data = experiments[exp_id]
        timestamps, values = [], []

        if metric in RESOURCE_METRICS:
            # Handle resource metrics
            start_time = exp_data['metadata'].get('start_time', 0)
            for resource_entry in exp_data.get('resources', []):
                timestamp = resource_entry.get('timestamp', 0)
                relative_time = (timestamp - start_time) / 60.0  # Convert to minutes

                if metric.startswith('gpu_'):
                    # Handle GPU metrics
                    gpu_data = resource_entry.get('gpu', [])
                    if gpu_data:
                        # Average across all GPUs
                        if metric == 'gpu_utilization_percent':
                            value = sum(gpu['utilization_percent'] for gpu in gpu_data) / len(gpu_data)
                        elif metric == 'gpu_memory_percent':
                            value = sum(gpu['memory_percent'] for gpu in gpu_data) / len(gpu_data)
                        elif metric == 'gpu_memory_used_mb':
                            value = sum(gpu['memory_used_mb'] for gpu in gpu_data) / len(gpu_data)
                        else:
                            continue
                        timestamps.append(relative_time)
                        values.append(value)
                else:
                    # Handle CPU/memory metrics
                    if metric in resource_entry:
                        timestamps.append(relative_time)
                        values.append(resource_entry[metric])
        else:
            # Handle log metrics
            for log_entry in exp_data['logs']:
                data = log_entry.get('data', {})
                if metric in data and 'step' in data:
                    timestamps.append(data['step'])
                    value = data[metric]
                    # Handle NaN values gracefully
                    if isinstance(value, (int, float)) and not (isinstance(value, float) and str(value) == 'nan'):
                        values.append(value)
                    else:
                        values.append(None)

        if timestamps and values:
            # Get experiment display name - prefer custom name, fallback to shortened ID
            custom_name = exp_data['metadata'].get('name')
            if custom_name:
                display_name = custom_name
            else:
                # Fallback to shortened experiment ID
                display_name = exp_id[:20] + '...' if len(exp_id) > 20 else exp_id

            fig.add_trace(go.Scatter(
                x=timestamps,
                y=values,
                mode='lines+markers',
                name=display_name,
                connectgaps=False  # Don't connect across NaN values
            ))

    # Determine x-axis label based on metric type
    x_label = 'Time (minutes)' if metric in RESOURCE_METRICS else 'Step'

    fig.update_layout(
        title=f'{metric}',
        xaxis_title=x_label,
        yaxis_title=metric,
        hovermode='x unified',
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.3)',
            griddash='dot'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.3)',
            griddash='dot'
        ),
        legend=dict(
            orientation='h',  # Horizontal legend
            yanchor='top',
            y=-0.15,  # Position below the plot
            xanchor='center',
            x=0.5,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        )
    )

    return fig.to_dict()
