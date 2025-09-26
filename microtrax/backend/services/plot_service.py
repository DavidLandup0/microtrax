from typing import Dict, List, Any
import plotly.graph_objects as go
from microtrax.constants import RESOURCE_METRICS


def create_metric_plot(experiments: Dict[str, Dict[str, Any]], selected_experiments: List[str], metric: str, x_axis: str = 'step') -> Dict:
    """Create a Plotly figure for a specific metric"""
    fig = go.Figure()

    # Check if this is a resource metric

    for exp_id in selected_experiments:
        if exp_id not in experiments:
            continue

        exp_data = experiments[exp_id]
        steps, times, values = [], [], []

        start_time = exp_data['metadata'].get('start_time', 0)

        # Extract data points
        for entries, is_resource in [(exp_data.get('resources', []), True), (exp_data.get('logs', []), False)]:
            if metric in RESOURCE_METRICS and not is_resource:
                continue
            if metric not in RESOURCE_METRICS and is_resource:
                continue

            for entry in entries:
                if is_resource:
                    timestamp = entry.get('timestamp', 0)
                    relative_time = (timestamp - start_time) / 60.0

                    if metric.startswith('gpu_'):
                        gpu_data = entry.get('gpu', [])
                        if not gpu_data:
                            continue
                        # Average across all GPUs
                        gpu_key = metric.replace('gpu_', '')
                        value = sum(gpu[gpu_key] for gpu in gpu_data) / len(gpu_data)
                        times.append(relative_time)
                        values.append(value)
                    elif metric in entry:
                        times.append(relative_time)
                        values.append(entry[metric])
                else:
                    data = entry.get('data', {})
                    if metric not in data:
                        continue

                    entry_step = data.get('step')
                    entry_timestamp = entry.get('timestamp', 0)

                    # Only include if we have the required x-axis data
                    if (x_axis == 'step' and entry_step is not None) or (x_axis == 'time' and entry_timestamp > 0):
                        if entry_step is not None:
                            steps.append(entry_step)
                        if entry_timestamp > 0:
                            times.append((entry_timestamp - start_time) / 60.0)

                        value = data[metric]
                        # Handle NaN values gracefully
                        if isinstance(value, (int, float)) and not (isinstance(value, float) and str(value) == 'nan'):
                            values.append(value)
                        else:
                            values.append(None)

        # Choose x-axis data based on mode and metric type
        if metric in RESOURCE_METRICS:
            x_data = times  # Resource metrics are always time-based
        else:
            x_data = times if x_axis == 'time' else steps

        if x_data and values:
            # Get experiment display name - prefer custom name, fallback to shortened ID
            custom_name = exp_data['metadata'].get('name')
            if custom_name:
                display_name = custom_name
            else:
                # Fallback to shortened experiment ID
                display_name = exp_id[:20] + '...' if len(exp_id) > 20 else exp_id

            fig.add_trace(go.Scatter(
                x=x_data,
                y=values,
                mode='lines+markers',
                name=display_name,
                connectgaps=False  # Don't connect across NaN values
            ))

    # Determine x-axis label
    x_label = 'Time (minutes)' if (metric in RESOURCE_METRICS or x_axis == 'time') else 'Step'

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
