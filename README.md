# FishPassage

The ```FishPass.py``` module provides a flexible way to model passage of fish populations from main stem origin points upstream into the terminal tributaries of a synthetic stream network. As the fish travel upstream from their origins, populations are reduced at user-defined barriers and at stream confluences. Proportional splitting of populations at stream confluences based on stream network attributes is possible, or populations can persist through confluences with no reduction. Upstream travel stops when the population reaches a user-defined threshold.


Main stems and terminal tributary origin points can be manually defined by the user, or the tool can identify these features provided the stream network reaches are joined with surrounding drainage units (ie, watersheds). Please read the tool documentation to learn more about the options available.


![readme_diagram](https://user-images.githubusercontent.com/99696041/236638019-64a12ef1-8a10-46e1-b6dc-3c4f6fa2779d.png)


All operations are tabular in nature. This means the user must perform all spatial analysis prior to using the tool. (See the notebook in this repository for an example of preprocessing operations using ```geopandas```.)




The tool requires that the user have:

- a stream network with upstream/downstream unit relationships defined as a table
- a collection of barriers georeferenced to stream network units and defined as a table

and either:

- drainage units (ie, watersheds) georeferenced to stream network units and defined as a table, OR
- a list of origin points georeferenced to stream network units




## Demo data

A sample dataset of stream network, watershed polygons, and beaver dam barriers for the Chena River area of Interior Alaska is included in this repository for demonstration. The ```FishPassageModel.ipynb``` notebook references this dataset. 

The environment file ```FishPass.yml``` will allow you to run the ```FishPassageModel.ipynb``` notebook, and contains Jupyter Lab 3.5.3. Build this environment if you do not currently have a method of running Jupyter notebooks. Otherwise, simply confirm that the following packages are installed in an existing environment capable of running Jupyter notebooks:

- ```geopandas``` 0.12.2
- ```pandas``` 1.5.3
- ```matplotlib``` 3.7.1

If you aren't interested in running the demo notebook and just want to use the ```FishPass.py``` module, the only package required is:

- ```pandas``` 1.5.3


