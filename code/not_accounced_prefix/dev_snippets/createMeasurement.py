from ripe.atlas.cousteau import (
  Traceroute,
  AtlasSource,
  AtlasCreateRequest
)

from datetime import datetime

ATLAS_API_KEY = "d21416e6-c74e-43af-88a5-1c57bb190cd7"

traceroute = Traceroute(
    af=4, #Address Family
    target="184.164.232.1",
    description="createMeasurementTests",
    protocol="ICMP",
    packets=1,
    paris=8,
    first_hop=30
)

source = AtlasSource(
    type="area",
    value="WW",
    requested=5
)

atlas_request = AtlasCreateRequest(
    start_time=datetime.utcnow(),
    key=ATLAS_API_KEY,
    measurements=[traceroute],
    sources=[source],
    is_oneoff=True
)

(is_success, response) = atlas_request.create()

print(is_success) #True
print(response) #{u'measurements': [27952507]}

