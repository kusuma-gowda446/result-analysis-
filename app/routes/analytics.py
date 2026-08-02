from flask import Blueprint, jsonify, render_template
from app.services.analytics_service import AnalyticsService
from app.utils.security import admin_required

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/')
@admin_required
def index():
    return render_template('admin/analytics.html')

@analytics_bp.route('/api/stats')
@admin_required
def get_stats_api():
    data = AnalyticsService.get_class_analytics()
    return jsonify(data)
