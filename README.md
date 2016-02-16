AFFEC Spider
============

AFFEC Spider is a tool for importing data from other agencies into AFFEC. The
spider is a plugin based tool containing Site and DB plugins. The different type
of plugins have an exposed interface, so if one site requires scraping and
another is kind enough to provide an API, the spider itself has a common API to
call upon to import data. Same with the database plugins. Whether the plugin is
for Salesforce or MySQL the exposed API is the same.

To setup a virtual environment is recommended in order to not clobber system
dependencies. You can read about them here: https://virtualenv.pypa.io/en/latest/

Getting python modules for a virtualenv sometimes requires a few system libraries
as well. Spider needs the following dev/devel packages:

python libxml2 libxslt zlib libjpeg

and possibly for some rare situations, the following as well:

libtiff openjpeg libwepb

The core spider dependencies are located in the top directory as requirements.txt.
Use `pip install -r requirements.txt` to install them. Each plugin being used
may have their own dependencies which should be located in their respective
top directories in a file called requirements.txt as well; be sure to install
those too.

To run the spider/data importer, execute:
```
python main.py
```

with your virtual environment activated.


Please feel free to email justin.noah@afamilyforeverychild.org with any issues
or questions you may have.
