import getpass
import glob
import os
import subprocess

import shutil

from HDR.Methods import Method
from Tool import Property


class Enfuse(Method):
    def stack(self, files):
        if(not os.path.exists("/tmp/hdr-%s" % getpass.getuser())):
            os.mkdir("/tmp/hdr-%s" % getpass.getuser())

        command = ["align_image_stack", "-m", "--gpu", "-a", "/tmp/hdr-%s/OUT_" % getpass.getuser()] + files
        subprocess.call(command)

        aligned_list = glob.glob("/tmp/hdr-%s/OUT*.tif" % getpass.getuser())
        aligned_list.reverse()
        return aligned_list


    def run(self, files, output, full_width, full_height):
        mask = self.props["mask"].options[self.props["mask"].get_value()].lower().replace(" ", "-")
        weight = self.props["weight"].options[self.props["weight"].get_value()].lower()
        colourspace = self.props["colourspace"].options[self.props["colourspace"].get_value()]

        command = ["enfuse", "--output=/tmp/hdr-stacked-%s.tiff" % getpass.getuser(),
                   "--%s" % mask,
                   "--exposure-weight-function=%s" % weight,
                   "--blend-colorspace=%s" % colourspace,
                   "--exposure-width=%.3f" % self.props["width"].get_value(),
                   "-v"] + files

        print(command)

        subprocess.call(command)

        shutil.copyfile("/tmp/hdr-stacked-%s.tiff" % getpass.getuser(), output)
        shutil.rmtree("/tmp/hdr-%s" % getpass.getuser())
        os.unlink("/tmp/hdr-stacked-%s.tiff" % getpass.getuser())

    def on_init(self):
        self.id = "Enfuse"
        self.name = "Enfuse"
        self.properties = [
            Property("weight", "Weight Function", "Combo", 0, options=[
                "Gaussian",
                "Lorentzian",
                "Half-Sine",
                "Full-Sine",
                "Bi-Square"
            ]),
            Property("mask", "Mask Type", "Combo", 0, options=[
                "Soft Mask",
                "Hard Mask"
            ]),
            Property("colourspace", "Blend Colourspace", "Combo", 0, options=[
                "CIECAM",
                "CIELAB",
                "CIELUV",
                "IDENTITY"
            ]),
            Property("width", "Exposure Width", "Spin", 0.2, min=0, max=1)
        ]