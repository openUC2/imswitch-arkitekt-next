import imswitch
from imswitch.imcontrol.model.managers.detectors.DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter
from imswitch.imcontrol.controller.basecontrollers import ImConWidgetController
from imswitch.imcontrol.view.ImConMainView import _DockInfo
from imswitch.imcommon.controller import MainController
from imswitch.imcommon.model.logging import initLogger
from imswitch.imcontrol.controller.controllers.LaserController import LaserController
from imswitch.imcommon.framework import Worker
import threading

import numpy as np
from arkitekt_next import easy
import time
from typing import Generator
from mikro_next.api.schema import Image, from_array_like

class imswitch_arkitekt_next_controller(ImConWidgetController):
    """Linked to CameraPluginWidget."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self.__logger.debug("Initializing imswitch arkitekt_next controller")
        
        # initalize arkitekt connection                
        self.app = easy("TEST", url="localhost")
        # bind functions to the app
        self.app.register(self.generate_n_string)
        self.app.register(self.upload_image)
        self.app.register(self.print_string)
        self.app.enter()
        
        self.__logger.debug("Start Arkitekt Runtime")
        threading.Thread(target=self.app.run).start()
        #self._serverWorker = ArkitektRuntime(self)
        #self._thread = threading.Thread(target=self._serverWorker.run)
        #self._thread.start()

        
    
    def generate_n_string(self, n: int = 10, timeout: int = 2) -> Generator[str, None, None]:
        """Generate N Strings

        This function generates {{n}} strings with a {{timeout}} ms timeout between each string


        Parameters
        ----------
        n : int, optional
            The number of iterations, by default 10
        timeout : int, optional
            The timeout, by default 2

        Returns
        -------
        str
            A string with Hello {n}
        """
        for i in range(n):
            print(i)
            time.sleep(timeout)
            yield f"Hello {i}"

    # Typehints are used to generate the schema for the function
    # you cannot omit the typehints, Image is a custom type that is used to represent images
    # that are stored on the mikro-next server
    # If you omit documentation, function names will be infered from the function name
    def upload_image(self, image_name: str) -> Image:
        return from_array_like(np.random.rand(100, 100, 3) * 255, name=image_name)

    def print_string(self, input: str) -> str:
        """Print String

        This function prints the input string to
        the console

        Parameters
        ----------
        input : str
            The input string

        Returns
        -------
        str
            The printed string
        """
        print(input)
        return input

class ServerThread(threading.Thread):
    def __init__(self, parent):
        super().__init__()
        self.server = None
        self.parent = parent

    def run(self):
        try:
            self.server = self.parent.app
            self.server.run()
        except Exception as e:
            print(f"Couldn't start server: {e}")

    def stop(self):
        if self.server:
            self.server.should_exit = True
            self.server.lifespan.shutdown()
            self.server
            print("Arkitekt Server is stopping...")
            
class ArkitektRuntime(Worker):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._paused = False
        self._canceled = False

        self.__logger =  initLogger(self)

    def moveToThread(self, thread) -> None:
        return super().moveToThread(thread)

    def run(self):
        # Create and start the server thread
        self.server_thread = threading.Thread(target=self.parent.app.run)# ServerThread(self.parent)
        self.server_thread.start()

    def stop(self):
        self.__logger.debug("Stopping arkitekt")
        try:
            self.server_thread.stop()
            #self.server_thread.join()
        except Exception as e:
            self.__logger.error("Couldn't stop server: "+str(e))




# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
