Sample queries related to quest definitions 
“Quest Maker” 
Context in app:
Query inputs 
An activities director at Riverside Park wants to launch a quest for a visiting school group on November 2, 2025 [arbitrary date in the future]. There is one specific area of the park where the group will be based.  What visible features will be on plants that day near paths in that area?  What quests/themes may link those traits? 
A person is out with the app up in Riverside Park in a given area on a day, what quests could be suggested?  I.e. what traits are visible
On the blue trail in Ward Pound Ridge Preserve in Westchester, NY, what traits can I look for with a visiting child today?  Or next month?
Query output …in each case the query would serve up and a decision system would organize content around  a List of quests organized around a theme of similar visible features, e.g. 
Flowers and grasses in bloom / in seed  (“Late bloomers [in a flower bed]”
Leaves visible: Trees that have lost leaves
Trees with buds visible 
Leaves not visible: Trees that still have leaves
…e.g. Could be a ‘how many trees have leaves now?
Tree habit: 
Understory/shorter trees (Many types of trees - the understory vs the overstory ) 
Tall trees 
Trees with alternating branches 
Bushes (trees with multiple stems and shorter habits)
Different types of bark
Winter food sources 
Trees that provide winter forage for animals or insects 

Input: 
App input: Place: Latitude, longitude
A single point
A path [array of latitude/longitude]  
Area [array of latitude/longitude, end point = starting point]
Data input: Plants in place: Input on plants visible from the place e.g. GBIF observations … or… Park-owned asset management system [ESRI]
…
Data input: Visible features on plants at the date
….
Data input: Themes-related data: other features of plants that can connect them into useful themes, et.g. 
Nature of the visible features - similarities or contrasts of simple
Animal interactions: what insects host, what birds
Plant “origin”
Plant chemistry: 
Carbon sequestration
Allelopathic plants
Plant interactions: 
Plant form typical of species 
Plant form reflecting environment 
Leaning branches, smaller branches over paths/compressed roots
Output: 
Plants in the area [grouped by trait attributes, themes of trait attributes, themes of plants]
Animals with more than one plant interaction
Origin
Historiy of plant 
Visible traits on those plants - grouped by similar values 
Trait name [e.g. “leaves on branch”]
Trait value [e.g. “opposite”]
Reference image of trait with that value
Phenology of trait [seasonal, lifespan of trait]
Images and timstamps of trait from iNat or other database that shows the trait instance on the plan plant 
Trait provenance
Rough Location (Lat, Long)
Theme category
Taxonomic bucket e.g. Genus (question here is how we want to treat taxonomic information)
What else (VW – Take a walk!)

