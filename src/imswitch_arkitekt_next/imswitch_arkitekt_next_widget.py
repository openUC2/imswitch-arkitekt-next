from imswitch.imcontrol.view.widgets.basewidgets import Widget

global_app = None
class imswitch_arkitekt_next_widget(Widget):
    """Linked to the arkitekt_next Controller ."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        