# bcmatools

A set of python 3.7+ scripts to unpack 3ds manual files (.bcma) to a XML representation, and back

## Usage

To unpack:
```
python3 extractor.py arc <your bcma file> <extraction folder>
python3 extractor.py bclyt <extraction folder> <output xml file>
```
To rebuild from a XML:
```
python3 creator.py <xml file> <output bcma file>
```

To insert the newly created bcma into a cia:
- rename it to `Manual.bcma` and place it in a folder, alone
- run the command `makerom -f cfa -o "<output cfa file>" -target t -rsf "<path to manual.rsf>" -DMANUAL_ROMFS="<path to folder containing Manual.bcma>"`
- and finally, when building your game/application cia, add `-content "<path to the cfa>:1:1"` at the end of the makerom command

## Requirements

For simply unpacking:  
`pip install lxml`  
To be able to repack a XML:  
`pip install -e ./nzlss_src`  
To use the editor:  
`pip install PySide2`  

## Inspirations and data sources

- For parsing the BCLYT files  
http://3dbrew.org/wiki/CLYT_format  
https://github.com/pleonex/Clypo  
https://github.com/shibbo/flyte  

- For unpacking darc files  
https://www.3dbrew.org/wiki/DARC  
https://github.com/yellows8/darctool  
https://github.com/magical/nlzss for decompression of darc files  
https://github.com/DorkmasterFlek/python-nlzss for compression of darc files  

## License

since the code used as inspiration was under the MIT or the GPLv3 (or 2+), this tool has to be under the GPLv3
