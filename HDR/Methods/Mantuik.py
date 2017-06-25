import getpass
import os
import subprocess

import shutil

from HDR.Methods import Method
from Tool import Property


class Mantuik06(Method):
    def stack(self, files):
        if(not os.path.exists("/tmp/hdr-%s" % getpass.getuser())):
            os.mkdir("/tmp/hdr-%s" % getpass.getuser())

        command = ["align_image_stack", "--gpu", "-a", "/tmp/hdr-%s/OUT_" % getpass.getuser(), "-o",
                   "/tmp/hdr-%s/OUT" % getpass.getuser()] + files

        print(command)
        subprocess.call(command)

        return ["/tmp/hdr-%s/OUT.hdr" % getpass.getuser(),]

    def run(self, files, output, full_width, full_height):

        command = "pfsin --radiance '%s' | pfstmo_mantiuk06 -f %.2f -s %.2f | pfsgamma --gamma %.2f | pfsout '%s'" % \
                  (files[0], self.props["contrast"].get_value(), self.props["saturation"].get_value(),
                   self.props["gamma"].get_value(), output)

        print(command)

        os.system(command)

        shutil.rmtree("/tmp/hdr-%s" % getpass.getuser())

    def on_init(self):
        self.id = "Mantuik06"
        self.name = "Mantuik '06"
        self.properties = [
            Property("contrast", "Contrast", "Slider", 0.1, min=0, max=1),
            Property("saturation", "Saturation", "Slider", 0.8, min=0, max=2),
            Property("gamma", "Gamma", "Slider", 2.0, min=0, max=3)
        ]


class Mantuik08(Method):
    def stack(self, files):
        if(not os.path.exists("/tmp/hdr-%s" % getpass.getuser())):
            os.mkdir("/tmp/hdr-%s" % getpass.getuser())

        command = ["align_image_stack", "--gpu", "-a", "/tmp/hdr-%s/OUT_" % getpass.getuser(), "-o",
                   "/tmp/hdr-%s/OUT" % getpass.getuser()] + files

        print(command)
        subprocess.call(command)

        return ["/tmp/hdr-%s/OUT.hdr" % getpass.getuser(),]

    def run(self, files, output, full_width, full_height):
        display = self.props["display"].options[self.props["display"].get_value()].lower().replace(" ", "_")
        saturation = self.props["saturation"].get_value()
        contrast = self.props["contrast"].get_value()

        command = "pfsin --radiance '%s' | pfstmo_mantiuk08 --display-function pd=%s -c%.2f -e%.2f | pfsout '%s'" % \
                  (files[0], display, saturation, contrast, output)

        print(command)

        os.system(command)

        shutil.rmtree("/tmp/hdr-%s" % getpass.getuser())

    def on_init(self):
        self.id = "Mantuik08"
        self.name = "Mantuik '08"
        self.properties = [
            Property("display", "Display", "Combo", 0, options=[
                "LCD",
                "LCD Office",
                "LCD Bright",
                "CRT"
            ]),
            Property("saturation", "Saturation", "Slider", 1, min=0, max=2),
            Property("contrast", "Contrast", "Slider", 1, min=0, max=10)
        ]