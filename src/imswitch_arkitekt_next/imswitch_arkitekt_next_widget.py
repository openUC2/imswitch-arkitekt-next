from imswitch.imcontrol.view.widgets.basewidgets import Widget
from imswitch.imcommon.model import initLogger
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

global_app = None
class imswitch_arkitekt_next_widget(Widget):
    """Linked to the arkitekt_next Controller ."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        