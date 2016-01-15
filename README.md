AFFEC Spider
============

AFFEC Spider is a tool for importing data from other agencies into AFFEC. The
spider is a plugin based tool containing Site and DB plugins. The different type
of plugins have an exposed interface, so if one site requires scraping and
another is kind enough to provide an API, the spider itself has a common API to
call upon to import data. Same with the database plugins. Whether the plugin is
for Salesforce or MySQL the exposed API is the same.
