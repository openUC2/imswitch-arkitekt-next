
from imswitch.imcommon.framework import Signal, SignalInterface
from imswitch.imcommon.model import initLogger
from imswitch.imcommon.model import dirtools
import os 
import json
class imswitch_arkitekt_next_manager(SignalInterface):

    def __init__(self, pluginInfo, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)

        # set  of parameters for autocompletion of the config file in case its not present
        self.allParameterKeys = ["token", "host", "port"]
        
        # get default configs
        self.arkitekt_config_filename = "config.json"
        # the config file is stored in the user directory e.g. ~/ImSwitchConfig/arkitekt-next/config.json
        self.defaultConfigPath = os.path.join(dirtools.UserFileDirs.Root, "arkitekt-next")
        if not os.path.exists(self.defaultConfigPath):
            os.makedirs(self.defaultConfigPath)
            self.writeDefaultConfig(self.defaultConfigPath)
        
        try:
            with open(os.path.join(self.defaultConfigPath, self.arkitekt_config_filename)) as jf:
                # check if all keys are present 
                self.defaultConfig = json.load(jf)
                # check if all keys are present 
                missing_keys = [key for key in self.allParameterKeys if key not in self.defaultConfig]
                if missing_keys:
                    raise KeyError
                else:
                    pass
                    
        except Exception as e:
            self.__logger.error(f"s {self.defaultConfigPath}: {e}")
            self.writeDefaultConfig()

    def writeDefaultConfig(self):
        # generate a default config file
        self.defaultConfig = {}
        self.defaultConfig["token"] = "your_token"
        self.defaultConfig["host"] = "go.arkitekt.live"
        self.defaultConfig["port"] = 8080
        self.writeConfig(self.defaultConfig)

    def updateConfig(self, parameterName, value):
        with open(os.path.join(self.defaultConfigPath, self.arkitekt_config_filename), "w") as outfile:
            mDict = json.load(outfile)
            mDict[parameterName] = value
            json.dump(mDict, outfile, indent=4)
            
    def writeConfig(self, data):
        with open(os.path.join(self.defaultConfigPath, self.arkitekt_config_filename), "w") as outfile:
            json.dump(data, outfile, indent=4)
