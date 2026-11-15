"""A world model of the cooling loop, and a policy learned inside it.

Nothing here touches a real loop. The model says how film grows, what it does
to the chip temperature, and what a dose clears; the policy learns when and
where to treat from what a sensor would report. Both are models, and the
numbers they produce are about the model, not about any site.
"""

from __future__ import annotations
