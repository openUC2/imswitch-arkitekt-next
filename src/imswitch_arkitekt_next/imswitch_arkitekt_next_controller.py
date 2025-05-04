import datetime
import imswitch
from imswitch.imcontrol.controller.basecontrollers import ImConWidgetController
from imswitch.imcommon.model.logging import initLogger
import threading
from psygnal import emit_queued
import numpy as np
import time
from typing import Generator
import xarray as xr
try:
    from koil.psygnal import signals_to_sync
    from mikro_next.api.schema import PartialRGBViewInput, ColorMap, AffineTransformationView, create_stage, PartialAffineTransformationViewInput
    from arkitekt_next import progress
    from arkitekt_next import easy
    from mikro_next.api.schema import Image, from_array_like
    IS_ARKITEKT = True
except ImportError:
    IS_ARKITEKT = False
    easy = None
    Image = None
    from_array_like = None
    PartialRGBViewInput = None
    
class imswitch_arkitekt_next_controller(ImConWidgetController):
    """Linked to CameraPluginWidget."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self.__logger.debug("Initializing imswitch arkitekt_next controller")
        if not IS_ARKITEKT:
            return 
        
        # self.mToken = self._master.pluginInfo.token
        
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.microscopeDetector = self._master.detectorsManager[
            allDetectorNames[0]
        ]  # FIXME: This is hardcoded, need to be changed through the GUI
        # initalize arkitekt connection                
        self.app = easy("TEST", url="go.arkitekt.live")
        # bind functions to the app
        self.app.register(self.generate_n_string)
        self.app.register(self.capture_latest_image)
        self.app.register(self.print_string)
        self.app.register(self.move_to_position)
        self.app.register(self.scan2DImageTiles)
        self.app.register(self.manual2DStageScan)
        self.app.register(self.tile_scan)
        # self.app.koil.uvify = False
        self.app.enter()
        self.active_stage = None
        
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]        
        self.pixelSizeXY = self.microscopeDetector.pixelSizeUm[-1]
        
        
        
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
    
    
    def capture_latest_image(self, image_name: str) -> Image:
        
        self.active_stage = create_stage("stage")
        
        # get the current position of the stage
        currentPos = self.stages.getPosition()
        print(currentPos)
        posX , posY = currentPos.get("X", 0), currentPos.get("Y", 0)
        
        
       
        affine_view = PartialAffineTransformationViewInput(
            affineMatrix=[
                [self.pixelSizeXY, 0, posX, 1],
                [0, self.pixelSizeXY, posY, 1],
                [0, 0, 1,   1],
                [0, 0, 0, 1]
            ],
            stage=self.active_stage
            
        )
        
        
        
        frame = self.microscopeDetector.getLatestFrame()
        if frame is None:
            return
        if len(frame.shape) == 2:
            frame = np.repeat(frame[:, :, np.newaxis], 3, axis=2)
            
            
        
        
        print("Frame")
        print(frame.mean())
        
        return from_array_like(xr.DataArray(frame, dims=list("xyc")), name=image_name, rgb_views=[
            PartialRGBViewInput(cMin=0, cMax=1, contrastLimitMax=frame.max(), contrastLimitMin=frame.min(), colorMap=ColorMap.RED, baseColor=[0, 0, 0]),
            PartialRGBViewInput(cMin=1, cMax=2, contrastLimitMax=frame.max(), contrastLimitMin=frame.min(), colorMap=ColorMap.GREEN, baseColor=[0, 0, 0]),
            PartialRGBViewInput(cMin=2, cMax=3, contrastLimitMax=frame.max(), contrastLimitMin=frame.min(), colorMap=ColorMap.BLUE, baseColor=[0, 0, 0])
        ], transformation_views=[
            affine_view
        ])
        
        
    def generate_snake_scan_coordinates(
        self, posXmin, posYmin, posXmax, posYmax, img_width, img_height, overlap
    ):
        #Generating snake scan coordinates, 0.2, 0.2, 3000.0, 3000.0, 400.0, 300.0, 20.0
        string = f"Generating snake scan coordinates, {posXmin}, {posYmin}, {posXmax}, {posYmax}, {img_width}, {img_height}, {overlap}"
        print(string)
        progress(0, string)
        # Calculate the number of steps in x and y directions
        steps_x = int((posXmax - posXmin) / (img_width * overlap))
        steps_y = int((posYmax - posYmin) / (img_height * overlap))

        print(steps_x, steps_y)
        coordinates = []

        # Loop over the positions in a snake pattern
        for y in range(steps_y):
            if y % 2 == 0:  # Even rows: left to right
                for x in range(steps_x):
                    coordinates.append([
                        (
                            posXmin + x * img_width * overlap,
                            posYmin + y * img_height * overlap,
                        ),
                        x,
                        y]
                    )
            else:  # Odd rows: right to left
                for x in range(
                    steps_x - 1, -1, -1
                ):  # Starting from the last position, moving backwards
                    coordinates.append([
                        (
                            posXmin + x * img_width * overlap,
                            posYmin + y * img_height * overlap,
                        ),
                        x,
                        y]
                    )

        return coordinates
    
    
    def move_to_position(self, x: int, y: int):
        """Move to position

        This function moves the stage to the given position

        Parameters
        ----------
        x : int
            The x position
        y : int
            The y position
        """
        self.stages.move(
            value=(x, y),
            axis="XY",
            is_absolute=True,
            is_blocking=True,
        )
        
        
    def tile_scan(
        self,
        minPosX: int,
        maxPosX: int,
        minPosY: int,
        maxPosY: int,
        overlap: int=0.75,
        nTimes: int =1,
        tSettle: float =0.05,
    ) -> Generator[Image, None, None]:
        """ Tile Scan"""

        initialPosition = self.stages.getPosition()
        initPosX = initialPosition["X"]
        initPosY = initialPosition["Y"]
        
        
        
        
        if not self.microscopeDetector._running:
            self.microscopeDetector.startAcquisition()

        # now start acquiring images and move the stage in Background
        mFrame = self.microscopeDetector.getLatestFrame()
        NpixX, NpixY = mFrame.shape[1], mFrame.shape[0]

        # starting the snake scan
        # Calculate the size of the area each image covers
        img_width = NpixX * self.microscopeDetector.pixelSizeUm[-1]
        img_height = NpixY * self.microscopeDetector.pixelSizeUm[-1]
        image_dims = (img_width, img_height)
        # precompute the position list in advance
        
        positionList = self.generate_snake_scan_coordinates(
            minPosX, minPosY, maxPosX, maxPosY, img_width, img_height, overlap
        )

        maxPosPixY = int((maxPosY - minPosY) / self.microscopeDetector.pixelSizeUm[-1])
        maxPosPixX = int((maxPosX - minPosX) / self.microscopeDetector.pixelSizeUm[-1])


        # perform timelapse imaging
        for i in range(nTimes):

            # move to the first position
            self.stages.move(
                value=positionList[0],
                axis="XY",
                is_absolute=True,
                is_blocking=True,
            )
            # move to all coordinates and take an image

            # Scan over all positions in XY
            for mIndex, iPos in enumerate(positionList):
                # update the loading bar
                self.currentPosition = iPos[0]  # use for status updates in the GUI
                self.currentPositionX = iPos[0][0]
                self.currentPositionY = iPos[0][1]
                self.positionList = positionList
                self.mScanIndex = mIndex
                progress(mIndex * 100 / len(positionList), f"Scanning {iPos}")

                self.stages.move(
                    value=self.currentPosition,
                    axis="XY",
                    is_absolute=True,
                    is_blocking=True,
                )
                time.sleep(tSettle)

                yield self.capture_latest_image(f"Scanning {self.currentPositionX} {self.currentPositionY} AT {i}")


            time.sleep(0.1)

        # return to initial position
        self.stages.move(
            value=(initPosX, initPosY),
            axis="XY",
            is_absolute=True,
            is_blocking=False,
            acceleration=(self.acceleration, self.acceleration),
        )
        
        
        
        

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
        # ensure result is in dimensions c, t, z, x, y
        if len(mResult.shape) != 5:
            mResult = np.expand_dims(mResult, axis=0)
            mResult = np.expand_dims(mResult, axis=0)
            mResult = np.expand_dims(mResult, axis=0)
        return from_array_like(mResult, name="Scan2DImageTiles")
        
    def manual2DStageScan(self):
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.microscopeDetector = self._master.detectorsManager[allDetectorNames[0]] # FIXME: This is hardcoded, need to be changed through the GUI
        mFrame = self.microscopeDetector.getLatestFrame()

        # select lasers and add to gui
        allLaserNames = self._master.lasersManager.getAllDeviceNames()
        if "LED" in allLaserNames:
            self.led = self._master.lasersManager["LED"]
        else:
            self.led = None
        self.led.setEnabled(1)
        self.led.setValue(255)
        
        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]        
        currentPos = self.stages.getPosition()
        posX, posY = 100,100
        self.stages.move(value=(posX, posY), axis="XY", is_absolute=True, is_blocking=False, acceleration=(self.acceleration,self.acceleration))


        # build crazy workflow 
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
