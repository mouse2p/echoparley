import json
from dataclasses import asdict

import numpy as np

from echoparley.units import codebook_usage, fit_unit_extractor

rng = np.random.default_rng(7)
features = np.vstack((rng.normal(-1, 0.1, (20, 4)), rng.normal(1, 0.1, (20, 4))))
identifiers = fit_unit_extractor(features, 2, 2, seed=7).extract(features)
print(json.dumps(asdict(codebook_usage(identifiers, 2)), sort_keys=True))
