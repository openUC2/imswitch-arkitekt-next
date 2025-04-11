
from imswitch.imcontrol.view.guitools.ViewSetupInfo import ViewSetupInfo as SetupInfo
from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger


class imswitch_arkitekt_next_manager(SignalInterface):

    def __init__(self, pluginInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        
        if pluginInfo is not None and pluginInfo.token is not None:
            self.mToken = pluginInfo.token
        else:
            self.mToken = "3Ibm9C2iPudqW5qJEtfTqFkhGQo23409j2fpFUrXtMk"
        
        
