import plotly.graph_objects as go
import plotly.express as px
import folium
from folium.plugins import MarkerCluster, HeatMap
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json


class CrisisVisualizationService:
    """Сервис для визуализации данных кризисных симуляций"""

    @staticmethod
    def create_crisis_timeline(results: List[Dict[str, Any]]) -> go.Figure:
        """Создание временной линии кризисных событий"""
        events = [r for r in results if r['event_type'] in ['crisis', 'emergency_response']]
        df = pd.DataFrame(events)
        fig = px.timeline(
            df,
            x_start="time",
            x_end="time",
            y="event_type",
            color="severity" if "severity" in df.columns else "event_type",
            hover_data=["details"],
            title="Таймлайн кризисных событий"
        )
        fig.update_layout(
            xaxis_title="Время (часы)",
            yaxis_title="Тип события",
            showlegend=True
        )
        return fig
    @staticmethod
    def create_network_map(
            network_data: Dict[str, Any],
            crisis_data: Optional[Dict[str, Any]] = None
    ) -> folium.Map:
        """Создание интерактивной карты транспортной сети"""
        center_lat = network_data.get('center', [55.7558, 37.6173])[0]
        center_lon = network_data.get('center', [55.7558, 37.6173])[1]
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles='cartodbpositron'
        )
        marker_cluster = MarkerCluster().add_to(m)
        for node in network_data.get('nodes', []):
            folium.Marker(
                location=[node['lat'], node['lon']],
                popup=f"Узел: {node.get('name', 'Unknown')}<br>"
                      f"Тип: {node.get('type', 'Unknown')}<br>"
                      f"Нагрузка: {node.get('load', 0):.1f}%",
                icon=folium.Icon(
                    color=CrisisVisualizationService._get_node_color(node),
                    icon=CrisisVisualizationService._get_node_icon(node),
                    prefix='fa'
                )
            ).add_to(marker_cluster)
        for edge in network_data.get('edges', []):
            start = next((n for n in network_data['nodes']
                          if n['id'] == edge['from']), None)
            end = next((n for n in network_data['nodes']
                        if n['id'] == edge['to']), None)
            if start and end:
                folium.PolyLine(
                    locations=[[start['lat'], start['lon']],
                               [end['lat'], end['lon']]],
                    color=CrisisVisualizationService._get_edge_color(edge),
                    weight=edge.get('weight', 2),
                    opacity=edge.get('opacity', 0.7),
                    popup=f"Связь: {edge.get('id', 'Unknown')}<br>"
                          f"Пропускная способность: {edge.get('capacity', 0)}<br>"
                          f"Загруженность: {edge.get('utilization', 0):.1f}%"
                ).add_to(m)
        if crisis_data:
            for zone in crisis_data.get('affected_zones', []):
                if zone['type'] == 'circle':
                    folium.Circle(
                        location=zone['center'],
                        radius=zone['radius_km'] * 1000,
                        color='red',
                        fill=True,
                        fill_color='red',
                        fill_opacity=0.2,
                        popup=f"Зона кризиса<br>"
                              f"Уровень опасности: {zone.get('severity', 0)}/5"
                    ).add_to(m)
        if network_data.get('traffic_data'):
            heat_data = [[n['lat'], n['lon'], n.get('load', 0)]
                         for n in network_data['nodes']]
            HeatMap(heat_data, radius=15).add_to(m)
        return m
    @staticmethod
    def create_performance_dashboard(metrics: Dict[str, Any]) -> Dict[str, go.Figure]:
        """Создание дашборда с метриками производительности"""
        figures = {}
        if 'vehicle_utilization' in metrics:
            fig = go.Figure()
            times = metrics['vehicle_utilization'].get('timestamps', [])
            utilization = metrics['vehicle_utilization'].get('values', [])
            fig.add_trace(go.Scatter(
                x=times,
                y=utilization,
                mode='lines+markers',
                name='Загруженность ТС',
                line=dict(color='blue', width=2)
            ))
            if 'crisis_events' in metrics:
                for event in metrics['crisis_events']:
                    fig.add_vline(
                        x=event['time'],
                        line_dash="dash",
                        line_color="red",
                        annotation_text=event['type']
                    )
            fig.update_layout(
                title="Динамика загруженности транспортных средств",
                xaxis_title="Время (часы)",
                yaxis_title="Загруженность, %",
                showlegend=True
            )
            figures['vehicle_utilization'] = fig
        if 'delivery_times' in metrics:
            fig = go.Figure()
            delivery_data = metrics['delivery_times']
            fig.add_trace(go.Box(
                y=delivery_data.get('values', []),
                name='Время доставки',
                boxmean=True,
                marker_color='green'
            ))
            fig.update_layout(
                title="Статистика времени доставки",
                yaxis_title="Время (часы)",
                showlegend=False
            )
            figures['delivery_times'] = fig
        if 'resource_distribution' in metrics:
            resource_data = metrics['resource_distribution']
            labels = list(resource_data.keys())
            values = list(resource_data.values())
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=.3,
                textinfo='label+percent'
            )])
            fig.update_layout(
                title="Распределение ресурсов"
            )
            figures['resource_distribution'] = fig
        if 'correlation_matrix' in metrics:
            corr_matrix = metrics['correlation_matrix']
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix['matrix'],
                x=corr_matrix['labels'],
                y=corr_matrix['labels'],
                colorscale='RdBu',
                zmid=0
            ))
            fig.update_layout(
                title="Корреляция метрик производительности",
                xaxis_title="Метрики",
                yaxis_title="Метрики"
            )
            figures['correlation_matrix'] = fig
        return figures
    @staticmethod
    def create_3d_network_visualization(network_data: Dict[str, Any]) -> go.Figure:
        """Создание 3D визуализации транспортной сети"""
        nodes = network_data.get('nodes', [])
        edges = network_data.get('edges', [])
        node_x = [n.get('x', 0) for n in nodes]
        node_y = [n.get('y', 0) for n in nodes]
        node_z = [n.get('z', 0) for n in nodes]
        node_text = [n.get('name', f"Node {i}") for i, n in enumerate(nodes)]
        node_size = [n.get('size', 10) for n in nodes]
        node_color = [n.get('color_value', 0.5) for n in nodes]
        node_trace = go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers',
            marker=dict(
                size=node_size,
                color=node_color,
                colorscale='Viridis',
                colorbar=dict(title="Нагрузка"),
                line=dict(color='rgb(50,50,50)', width=0.5)
            ),
            text=node_text,
            hoverinfo='text'
        )
        edge_x = []
        edge_y = []
        edge_z = []
        for edge in edges:
            start_node = next((n for n in nodes if n['id'] == edge['from']), None)
            end_node = next((n for n in nodes if n['id'] == edge['to']), None)
            if start_node and end_node:
                edge_x.extend([start_node.get('x', 0), end_node.get('x', 0), None])
                edge_y.extend([start_node.get('y', 0), end_node.get('y', 0), None])
                edge_z.extend([start_node.get('z', 0), end_node.get('z', 0), None])
        edge_trace = go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(
                color='rgb(125,125,125)',
                width=edge.get('width', 1) if edges else 1
            ),
            hoverinfo='none'
        )
        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title='3D визуализация транспортной сети',
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            showlegend=False
        )
        return fig
    @staticmethod
    def create_animated_crisis_development(
            simulation_results: List[Dict[str, Any]]
    ) -> go.Figure:
        """Создание анимированного графика развития кризиса"""
        time_slices = {}
        for result in simulation_results:
            if result['event_type'] == 'metrics_snapshot':
                time = result['time']
                if time not in time_slices:
                    time_slices[time] = []
                time_slices[time].append(result['data'])
        frames = []
        for time, data_list in sorted(time_slices.items()):
            crisis_intensity = np.mean([d.get('crisis_intensity', 0)
                                        for d in data_list])
            vehicle_utilization = np.mean([d.get('vehicle_utilization', 0)
                                           for d in data_list])
            delivery_delays = np.mean([d.get('delivery_delays', 0)
                                       for d in data_list])
            frame = go.Frame(
                data=[
                    go.Scatter3d(
                        x=[time],
                        y=[crisis_intensity],
                        z=[vehicle_utilization],
                        mode='markers',
                        marker=dict(
                            size=10 + delivery_delays * 5,
                            color=delivery_delays,
                            colorscale='RdYlGn_r',
                            showscale=True
                        )
                    )
                ],
                name=f"t={time:.1f}"
            )
            frames.append(frame)
        fig = go.Figure(
            data=[go.Scatter3d(
                x=[0],
                y=[0],
                z=[0],
                mode='markers',
                marker=dict(
                    size=10,
                    color=0,
                    colorscale='RdYlGn_r'
                )
            )],
            frames=frames
        )
        fig.update_layout(
            title="Анимированное развитие кризисной ситуации",
            scene=dict(
                xaxis_title='Время (часы)',
                yaxis_title='Интенсивность кризиса',
                zaxis_title='Загруженность ТС',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            updatemenus=[dict(
                type="buttons",
                buttons=[dict(
                    label="Play",
                    method="animate",
                    args=[None, dict(
                        frame=dict(duration=500, redraw=True),
                        fromcurrent=True,
                        mode='immediate'
                    )]
                )]
            )]
        )
        return fig
    @staticmethod
    def _get_node_color(node: Dict[str, Any]) -> str:
        """Определение цвета маркера узла"""
        load = node.get('load', 0)
        if load > 80:
            return 'red'
        elif load > 60:
            return 'orange'
        elif load > 40:
            return 'yellow'
        elif load > 20:
            return 'lightgreen'
        else:
            return 'green'
    @staticmethod
    def _get_node_icon(node: Dict[str, Any]) -> str:
        """Определение иконки узла"""
        node_type = node.get('type', '').lower()
        if 'warehouse' in node_type:
            return 'warehouse'
        elif 'port' in node_type:
            return 'anchor'
        elif 'airport' in node_type:
            return 'plane'
        elif 'rail' in node_type:
            return 'train'
        else:
            return 'circle'
    @staticmethod
    def _get_edge_color(edge: Dict[str, Any]) -> str:
        """Определение цвета ребра"""
        utilization = edge.get('utilization', 0)
        if utilization > 80:
            return 'red'
        elif utilization > 60:
            return 'orange'
        elif utilization > 40:
            return 'yellow'
        elif utilization > 20:
            return 'lightblue'
        else:
            return 'blue'