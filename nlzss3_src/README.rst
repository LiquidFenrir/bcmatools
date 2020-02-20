PyNLZSS3
=======

Python bindings for the Nintendo GBA/DS (and 3DS) LZSS compression algorithm.

LZSS algorithm and C code from CUE's tools: http://www.romhacking.net/utilities/826/

Installation
------------

::

    pip install -e .

Encode
------

::

    >> import nzlss3
    >> compressed_buffer = nzlss3.compress(buffer)

That's it!
