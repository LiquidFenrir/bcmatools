# Python package for Nintendo LZSS encoding/decoding - setup.py
#
# Copyright (C) 2017
#
#     Nintendo LZSS algorithm: CUE
#     Python package: Dorkmaster Flek <dorkmasterflek@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from setuptools import setup, Extension

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(name="nlzss3",
      version='0.2.0',
      description="Nintendo LZSS compression algorithm for Python 3",
      author="Cue, Dorkmaster Flek, LiquidFenrir",
      author_email="dorkmasterflek@gmail.com",
      maintainer="LiquidFenrir",
      maintainer_email="liquidfenrir@outlook.fr",
      license="GNU GPL v3",
      python_requires=">=3",
      ext_modules=[Extension(
            "nlzss3",
            sources=["pynlzss3.c", "lib/nlzss3.c"],
            include_dirs=['./include'],
            language="C")],
      long_description=long_description)
