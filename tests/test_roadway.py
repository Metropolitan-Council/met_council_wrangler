import os

import pytest

from cube_wrangler.roadway import Parameters, ModelRoadwayNetwork
from network_wrangler import RoadwayNetwork

def test_load(request):
    """
    """
    print("\n--Starting:", request.node.name)