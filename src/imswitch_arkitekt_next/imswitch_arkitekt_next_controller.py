import imswitch
from imswitch.imcontrol.model.managers.detectors.DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter
from imswitch.imcontrol.controller.basecontrollers import ImConWidgetController
from imswitch.imcontrol.view.ImConMainView import _DockInfo
from imswitch.imcommon.controller import MainController
from imswitch.imcommon.model.logging import initLogger
from imswitch.imcontrol.controller.controllers.LaserController import LaserController
from imswitch.imcommon.framework import Worker
from imswitch.imcommon.model import APIExport
from koil.psygnal import signals_to_sync
import threading
from psygnal import emit_queued

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
        self.app.register(self.scan2DImageTiles)
        # self.app.koil.uvify = False
        self.app.enter()
        self.__logger.debug("Start Arkitekt Runtime")
        
        # This wraps the signals into a (koiled) synchronous function that can be called from any subthread
        # as koiled-functions can also listen to cancelations we propagate the cancel signal to another thread
        # and set cancel_event when the signal is received
        self._commChannel.sigStartTileBasedTileScanning = signals_to_sync(self._commChannel.sigStartTileBasedTileScanning, 
                                                                          self._commChannel.sigOnResultTileBasedTileScanning)
        self.handle = self.app.run_detached()


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

    def scan2DImageTiles(self, numberTilesX = 3, numberTilesY = 3, stepSizeX = 300, stepSizeY = 300, nTimes = 1, tPeriod = 1, illuSource = 0, initPosX = 0, initPosY = 0, isStitchAshlar = False, isStitchAshlarFlipX = True, isStitchAshlarFlipY = True) -> Image:
        """ Scan 2D Image Tiles 
        
        This function scans 2D image tiles with the given parameters
        numberTilesX: int - The number of tiles in the x direction
        numberTilesY: int - The number of tiles in the y direction
        stepSizeX: float - The step size in the x direction
        stepSizeY: float - The step size in the y direction
        nTimes: int - The number of times to scan
        tPeriod: float - The period of time between each scan
        illuSource: int - The illumination source
        initPosX: float - The initial position in the x direction
        initPosY: float - The initial position in the y direction
        isStitchAshlar: bool - Should we stitch the ashlar
        isStitchAshlarFlipX: bool - Should we flip the ashlar in the x direction
        isStitchAshlarFlipY: bool - Should we flip the ashlar in the y direction
        
        should return the image
        """
        #lambda numberTilesX, numberTilesY, stepSizeX, stepSizeY, nTimes, tPeriod, illuSource, initPosX, initPosY, isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY: self._commChannel.sigStartTileBasedTileScanning.emit(numberTilesX, numberTilesY, stepSizeX, stepSizeY, nTimes, tPeriod, illuSource, initPosX, initPosY, isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY)
        mResult = np.random.rand(1, 1, 3, 100, 100) * 255 #  c, t, z, x, y
        
        if 1:
            numberTilesX = 3    
            numberTilesY = 3
            stepSizeX = 300
            stepSizeY = 300
            nTimes = 1
            tPeriod = 1
            illuSource = 0
            initPosX = 0
            initPosY = 0
            isStitchAshlar = False
            isStitchAshlarFlipX = True
            isStitchAshlarFlipY = True

        mResult = self._commChannel.sigStartTileBasedTileScanning(numberTilesX, numberTilesY, stepSizeX, stepSizeY, nTimes, tPeriod, illuSource, initPosX, initPosY, isStitchAshlar, isStitchAshlarFlipX, isStitchAshlarFlipY)
        return from_array_like(mResult, name="Scan2DImageTiles")
        
    def on_close(self):
        self.app.cancel()
        self.app.exit()



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
