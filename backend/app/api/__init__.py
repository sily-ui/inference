"""
API路由模块
"""

from flask import Blueprint

graph_bp = Blueprint('graph', __name__)
simulation_bp = Blueprint('simulation', __name__)
report_bp = Blueprint('report', __name__)
social_bp = Blueprint('social', __name__, url_prefix='/social')
prediction_bp = Blueprint('prediction', __name__, url_prefix='/prediction')

from . import graph  # noqa: E402, F401
from . import simulation  # noqa: E402, F401
from . import report  # noqa: E402, F401
from . import social  # noqa: E402, F401
from . import prediction  # noqa: E402, F401

