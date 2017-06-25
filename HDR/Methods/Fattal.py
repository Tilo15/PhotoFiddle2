import getpass
import os
import subprocess

import shutil

import cv2

from HDR.Methods import Method
from Tool import Property


class Fattal(Method):
    def stack(self, files):
        if(not os.path.exists("/tmp/hdr-%s" % getpass.getuser())):
            os.mkdir("/tmp/hdr-%s" % getpass.getuser())

        command = ["align_image_stack", "--gpu", "-a", "/tmp/hdr-%s/OUT_" % getpass.getuser(), "-o",
                       "/tmp/hdr-%s/OUT" % getpass.getuser()] + files

        print(command)
        subprocess.call(command)

        return ["/tmp/hdr-%s/OUT.hdr" % getpass.getuser(),]

    def run(self, files, output, full_width, full_height):
        im = cv2.imread(files[0], 2 | 1)
        ph, pw = im.shape[:2]
        cv2.imwrite(files[0], cv2.resize(im, (int(full_width), int(full_height)), interpolation = cv2.INTER_AREA))


        command = "pfsin --radiance '%s' | pfstmo_fattal02 -b %.2f -g %.2f -s %.2f -n %.2f -d %.2f -w %.2f -k %.2f -- | pfsout '%s'" % \
                  (files[0],
                   self.props["beta"].get_value(),
                   self.props["gamma"].get_value(),
                   self.props["saturation"].get_value(),
                   self.props["noise"].get_value(),
                   self.props["detail"].get_value(),
                   self.props["white"].get_value(),
                   self.props["black"].get_value(),
                   "/tmp/hdr-out-%s.tiff" % getpass.getuser())

        print(command)
        os.system(command)

        im = cv2.imread("/tmp/hdr-out-%s.tiff" % getpass.getuser(), 2 | 1)
        cv2.imwrite(output, cv2.resize(im, (int(pw), int(ph)), interpolation=cv2.INTER_AREA))

        os.unlink("/tmp/hdr-out-%s.tiff" % getpass.getuser())
        shutil.rmtree("/tmp/hdr-%s" % getpass.getuser())

    def on_init(self):
        self.id = "Fattal"
        self.name = "Fattal"
        self.properties = [
            Property("beta", "Beta", "Slider", 0.9, min=0.6, max=1),
            Property("gamma", "Gamma", "Slider", 0.8, min=0.1, max=1),
            Property("saturation", "Saturation", "Slider", 0.8, min=0.1, max=1),
            Property("detail", "Lightness", "Slider", 3, min=0, max=9),
            Property("noise", "Noise Reduction", "Slider", 0.0, min=0, max=1),
            Property("white", "Overexposure", "Slider", 0.5, min=0, max=1),
            Property("black", "Underexposure", "Slider", 0.5, min=0, max=1),

        ]
