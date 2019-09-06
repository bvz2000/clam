proper documentation coming once clam enters beta.

env vars that clam understands:

CLAM_CONFIG_PATH

CLAM_LANGUAGE


INSTALLATION
-
This package should be downloaded and placed somewhere on disk (Linux and MacOS ony at the moment).

Assume you store the root of this package in the following location (I am not recommending this specifically, but it should work):

/Applications/clam

Then you should add the following path to your PYTHONPATH env variable:

/Applications/clam/modules

You will also, of course, have to ensure that Clarisse is reading your PYTHONPATH variable.


In addition to this package, you will also have to download and install:

squirrel

https://github.com/bvz2000/squirrel

and


libClarisse

https://github.com/bvz2000/libClarisse