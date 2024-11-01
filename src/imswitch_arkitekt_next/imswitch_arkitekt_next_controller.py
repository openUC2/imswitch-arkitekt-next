import imswitch
from imswitch.imcontrol.model.managers.detectors.DetectorManager import DetectorManager, DetectorAction, DetectorNumberParameter
from imswitch.imcontrol.controller.basecontrollers import ImConWidgetController
from imswitch.imcontrol.view.ImConMainView import _DockInfo
from imswitch.imcommon.controller import MainController
from imswitch.imcommon.model.logging import initLogger
from imswitch.imcontrol.controller.controllers.LaserController import LaserController
import numpy as np
from arkitekt_next import register, easy
import time
from typing import Generator


class imswitch_arkitekt_next_controller(ImConWidgetController):
    """Linked to CameraPluginWidget."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__logger = initLogger(self)
        self.__logger.debug("Initializing imswitch arkitekt_next controller")
        self.run()

    # You can register your functions by using the @register decorator
    # functions always run in a threadpool and are not blocking 
    # all functions must be registered before the run function is called
    @register
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

    @register
    def upload_image(self, image_name: str) -> Image:
        return from_array_like(np.random.rand(100, 100, 3) * 255, name=image_name)




    # 
    @register
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



    # This is the part that runs the server
    # Everything must be registered before this function is called


    # The easy function is a context manager as it will need to clean
    # up the resources it uses when the context is exited (when the user stops the app)
    # make sure to give your app a name, (and the url/ip of the arkitekt server) 
    def run(self):
        e = easy("TEST", url="localhost")

        # If you want to perform a request to the server before enabling the
        # provisioning loop you can do that within the context

        # from_array_like(np.random.rand(100, 100, 3) * 255, name="test")
        # would upload an image to the server on app start

        # e.run() will start the provisioning loop of this app
        # this will block the thread and keep the app running until the user
        # stops the app (keyboard interrupt)
        e.run()

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
