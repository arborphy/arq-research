

**Arborphy App, Data Service \+ Reference Data Overview**

[0\. Near term product goals](#0.-near-term-product-goals)

[0.1:  “Calibrated Key” Def/Building](#0.1:-“calibrated-key”-def/building)

[0.2  Co-Ocurrence \+ Community Queries:  Declared and Inferred](#0.2-co-ocurrence-+-community-queries:-declared-and-inferred)

[A. Product Overview: Dynamic Field Guide (and the “Underlying Data service” )](#product-overview:-dynamic-field-guide-\(and-the-“underlying-data-service”-\))

[● End-user App description](#end-user-app-description)

[● Data service description](#data-service-description)

[B. Data Input Descriptions](#data-input-descriptions)

[2\. Evolving External data](#evolving-external-data)

[3\. Reference data Overview](#reference-data-overview)

[4\. Derived reference data, e.g. Calibrated Keys](#derived-reference-data,-e.g.-calibrated-keys)

[C. Reference data abstraction/modeling : Plant, Feature, Feature\_value sets](#synonyms,-verbalizations-expressing-relationships)

[D. Reference Model Preliminary Sketch](#d.-reference-model-preliminary-sketch)

## **0\. Near term product goals** {#0.-near-term-product-goals}

###  **0.1:  “Calibrated Key” Def/Building**  {#0.1:-“calibrated-key”-def/building}

- Calibration of Feature-Value-Model:  Hypothesis that extant affordable v-LLM’s can work for this   
  - What:  species \-\> {Feature, Feature\_value} sets \[feature/value vocabulary\] w/  reference image at  each key/feature and each leaf/feature+value \[or critical numbers of them\]  
    - The reference image may depend on a model and scaffolding M.O.   
      - {(v-LLM model\]), (prompt scaffold), \[species \-\> {Feature, Feature\_value}\] }   
        - v-LLM includes model and parameters and context   
          - Prompt scaffold will include verbalization generation m.o.   
        - Anchored / tested with a  set of  test images of the species in which the item is seen  
      - *TL;DR:*  
        - The feature vocabulary is “calibrated” with the LLM+ ‘cause it can recognize the Feature and values in the reference images   
      - Reference images  
        - By {feature, value} \- ? also by species ?  
        - …gathering exercise …  
      - Reference vocabularies  
        - TRY \- TBD  
        -  GoBotany by-species data normalized  
          - E.g. start looking by taxons   
          - Start with subsets of what’s visible \-   
        - GoBotany simple key that can be scraped  
    - **Coherent calibrated key:**   
      - Get coherence across feature vocabularies  using v-LLM equivalence  
        - If every reference image of (Feature+Value)\_1 can also be “seen” by the LLM as (feature,value\_2) then we’d say thos can be combined into a “equivalence class”  
        - LLM to say “is this feature visible” … find a reference image that shows the feature on a trusted botanical source…  
          -   
    - Process will need to iterate through/testing  
      - t1. Within every species+feature+value set: {Feature\_i, Feature\_Value\_{i,j}} and {Reference images} across species    
      - t2. …Across Sets features+values , or subsetting…. e.g. From different keys   
      - t3. Model perception validation:   
        - Possible feature hierarchy and sets of values admissible to trait to calibrate what model can “see” , or to prime the model in the prompt  
      - t4. Component: models, settings, etc  
    - Types of answers  
      - How robust is the key to to models and prompt scaffold   
        - Ideally, robustness across multiple of both of these  
      - What feature+value sets work best

  ### **0.2  Co-Ocurrence \+ Community Queries:  Declared and Inferred**  {#0.2-co-ocurrence-+-community-queries:-declared-and-inferred}

-  INaturalist derived plant instances, co-occurences & populations  
  - Demo of RAI capabilities on iNat observation data  
1. Source data: (i) RefData: Detection of  NY State Plant Communities; (ii) non-Ref:  iNat observations  
- 1a. Analysis of NY STate Plant Communities relevant  
  - T1. Overlap species   
  - T2. Distinct species   
  - ….for the future not now: T3? \[to add?  \+ physical environment  items , would need to be added to descriptions \]  
- 1b. Based on iNat observation \+ species extracts analyzed, identify “parts of park” that represent distinct communities   
  - Will require some GIS decisions about what parts are ….  
- 1c. Contribute inferred ID from community information   
  - If parts of the park look like NYS communities, what other species are expected  
    - Are those actually seen?  
    - …..?In reserve? Are there unidentified observations that could be identified in part with suggestions form   
- Source: ([website here](https://guides.nynhp.org/communities/), [book here](https://guides.nynhp.org/communities/) \- extraction in progress)  
- Bottom line obj: Discover capabilities and limitations with this data. Get oriented on/show proof of concept on how we can accomplish the above objectives  
2. From iNat: Inferred Co-occurence / Community  
   - What species co-occur in some area?   
     - Can we infer plant communities that are partially aligned or exist 

1. ## **Product Overview: Dynamic Field Guide (and the “Underlying Data service” )** {#product-overview:-dynamic-field-guide-(and-the-“underlying-data-service”-)}

* ### **End-user App description**  {#end-user-app-description}

  * App provides visual front end to data queries served the Data Service   
  * User perspective:  
    * What cool stuff can I be looking out for among the plants/trees in my park?   
    * Or ..  Curate a plant scavenger hunt in my local park today  \[or next month\] \- or a set of scavenger hunts for a teams of students \+ chaperones   
    * Or … Send me on a focused citizen science data gathering task to find instances of X plant or Y insect that pollinates ….  
      * List of specific plant communities and instances based on predictions from previous observations and structured information about the characteristics (features, etc) of the plants  
      * User might see  
        * Map for a treasure hunt  
        * Scavenger-hunt style lists to search for  
      * Validation that I see what you point me towards  
        * Photo \+ analysis   
        * May include GIS or RF confirmation of place

          

* ### ***Data*** **service description**  {#data-service-description}

  * Input:    
    * date \+ place   
    * Output:   
      * Arrays of    
      * plant type \+ instance of plant/community  \+ visible features \+ feature descriptions \+  accessory information derived from other features \+ reference images   
        * Summer: flowers in bloom on herbaceous plants and trees, leaves of different shapes emerging  
          * “Accessory” information linking : bee pollinated plants, medicinal uses, naturalized plants  
        * Winter: leaf buds on trees showing alternating vs. opposite patterns, dead stalks and seed heads from wildflowers, evergreen pine, evergreen herbaceous plants, (late winter) emerging plants

2. ## **Data Input Descriptions**  {#data-input-descriptions}

1. ***App-sourced data (input by user, sourced from user device)***  
   * Entered by user  
     * “Quest” Location \- target destination among curated set  
     * Check off items seen/experienced  
     * “Field notes”   
   * Ingested from user mobile device (TBD)   
     * User device location: GIS or RF-tag-proximate   
     * Photo images (not in initial draft)

     

2. ### **Evolving External data**   {#evolving-external-data}

   * Batch processed  
     * iNaturalist plant observations with “identifications” for some set of species in a location  
       * To be inferred: co-occurence data \- plant+plant   
     * Park location information  
     * Park plant community or instances project  ..  
       * New planting of X in Y location   
     * Historical seasonal/weather information \[maybe inferred from observation series

     

3. ### ***Reference*** **data Overview** {#reference-data-overview}

   * **Sources: extant field guides and botanical authoritative publications and sites, published tabular data**  
   * Field guide reference information: Associate  **sets of species with sets of Features** (e.g. leaf shape) **and Values** (e.g. lobed)    
     * Usually apply to sets of plants in some particular region and season  
     * Usually don’t track seasonal variations or lifecycle variations  \- e.g. look for these shape flowers \- in some plants those persist in some form through winter, in others they disappear entirely   
   * Horticultural data:  Environment (soil/sun/weather) compatibility, seasonality (flower time), lifecycle (perennial, annual, long-lived, growth rate, etc)  
     * E.g. acidic soil   
     * Leaf shape is only visible in winter for evergreen \+ marascent plants (latter means keep dead leaves on them), not for fully deciduous plants  
     * Attach as additional feature or make feeture, value triples  
   * Feature hierarchies \-   
     * Relate features or feature values to each other in e.g. parts, sub-parts  
       * Anatomical parts/subparts (leaves \-\> leaf arrangement \-\> leaf blade shape \-\> { leaf apex, leaf base, leaf margin }  
       * Seasonality parts/subparts: herbaceous \-\> perennial \-\> { evergreen, deciduous \-\> {ephemeral, marscent, persistent} }

       

4. ### **Derived reference data, e.g. Calibrated Keys**  {#derived-reference-data,-e.g.-calibrated-keys}

   * Keys that are vision-LLM compatible, relevant to the plants, feature, value  – adapted from external sources  
   * Humans can see them, vision-LLM model can distinguish \- is the trait (e.g. leaf arrangement ) visible? Is the leaf arrangement alternating?  
     * Extant keys (per above) , Feature hierarchies   
   * Inferred instances from iNat observations \- see above 0.1

   ## **C. Reference data abstraction/modeling : Plant, Feature, Feature\_value sets** {#synonyms,-verbalizations-expressing-relationships}

   * ## Keys for naturalists FROM TEXTS {#synonyms,-verbalizations-expressing-relationships}

     * ## E.g. Trees of the Northeast, wildflowers of New England {#synonyms,-verbalizations-expressing-relationships}

   * ## For the set of plants, they enumerate a set of features to  notice, and categorize the feature “values” into e.g. “leaf arrangement” “alternate” ,“opposite”, “whorled”  {#synonyms,-verbalizations-expressing-relationships}

     * ## In notation: {#synonyms,-verbalizations-expressing-relationships}

       * ## \\{Plant\_{k} \\}, k=1,..,N\_{plant} {#synonyms,-verbalizations-expressing-relationships}

         * ## Plants represent some kinda grouping that makes sense, often species, sometimes a cultivar or maybe a genus {#synonyms,-verbalizations-expressing-relationships}

           * ## Newcomb: 1,375 species (as of the time of its writing), tho some have merged and some divided since the original book {#synonyms,-verbalizations-expressing-relationships}

       * ## \\{Feature\_j, Value\_{j,k}\\}   {#synonyms,-verbalizations-expressing-relationships}

         * ## Feature\_j, is some set of features,  {#synonyms,-verbalizations-expressing-relationships}

           * ##  Newcomb four features: “Flower Symmetry”, “Plant Type”, “Leaf type”, “Leaf arrangement”  {#synonyms,-verbalizations-expressing-relationships}

         * ## where Value\_{j,k}  \\in { V\_{1},..,V\_{N\_{feature}}} where N\_{Feature} \<\<  N\_{plants}  {#synonyms,-verbalizations-expressing-relationships}

           * ## Newcomb: e.g. “Plant Type” values are {“Wildflowers”, “Shrubs”, “Vines”} {#synonyms,-verbalizations-expressing-relationships}

           * ## Total of 192 distinct Feature, Value combinations – the guide points to additional distinguishing features are described at the “leaf” level  {#synonyms,-verbalizations-expressing-relationships}

   * ## Feature \+ Value hierarchies  {#synonyms,-verbalizations-expressing-relationships}

     * ## *Source: From field guide, horticulture and botanical references* {#synonyms,-verbalizations-expressing-relationships}

     * ## Feature and Value relationships to enable verbalizations for human and machine recognition  {#synonyms,-verbalizations-expressing-relationships}

       * ## E.g. Inflorescence \-\> Flower \-\> \[ Flower Symmetry, Petal color, Petals, Stamen, Bracts etc\] {#synonyms,-verbalizations-expressing-relationships}

       * ## E.g. Leaves \-\> {Leaf arrangement, { Leaf Blade Shape : \[ Leaf Margin, Leaf Apex, Leaf Base \] }}  {#synonyms,-verbalizations-expressing-relationships}

       * ## Hairy \-\> 5 types of leaf hair …. Not hairy \-\> three types of shiny leaves {#synonyms,-verbalizations-expressing-relationships}

         ##  {#synonyms,-verbalizations-expressing-relationships}

     * ## Reference images for various  \[Plant, Feature, Feature\_value\]  {#synonyms,-verbalizations-expressing-relationships}

       * ## IMages with reference illustrations \+ tagged photos from trustworthy sites {#synonyms,-verbalizations-expressing-relationships}

       * ## Synonyms, Verbalizations expressing relationships  {#synonyms,-verbalizations-expressing-relationships}

       * ## Facilitated by feature hierarchies 

   ## 

   ## **D. Reference Model Preliminary Sketch** {#d.-reference-model-preliminary-sketch}

* Field guides and botanical studies often break down how pants look in terms of “triats” of those plants and assign values to those  
  * They also focus on sets of plants across some biological and/or regional set  
* Field guides describing plants in terms of sets of those traits, and a set of possible values 

   
Plant / Organism / Object ‘type’/’group’ 	

* ***P***  
  * ?? Could use ***O*** for “object of interset” or “organism of interest”   
  * When in an enumerated set ***P\_{i\_{P}} or P\_{k}*** , can be species, cultivars, genus, a set of observed species  
* ***P***’s represent ways of grouping individual instances of plants (or organisms or species)  
* Categorical set of admissible plant/plant groups specified somewhere  
  * For each model, there maybe an enumerated, admissible set  
    * Taxons: Species, sub-species (varieties), Genera (groups of species)  
    * Recognized Plant communities: Talus slope community includes a list of common species   
    * Inferred plant communities or co-occurence groups 

  				

  Plant / Organism / Object 	

* ***I*** (capital I)  
  * When enumerated  ***I\_{i\_{I} }*** , which may be observations that illustrate features of groups  
* The reality is that groups relate to instances which are often transitory (e.g. annual flowers that die and may or may not reseed)  
  * Tree or longer-lived organisms may 

  Plant instances identified as species (Predicate ID)

* ***I***  \[isType\] ***P***  
* E.g.   
  - Plant in my garden  I \[isType\]   P  \=  “Hypericum prolificum”   
    - Ground truth from cultivator , maybe it’s a clone of a genetically verified ??

  Features

* ***F***  
  * Aspects of plants that can be anatotomical and have descriptions   
  * E.g.  “Leaf shape” , “Leaf length”, “Leaf Stem” , “Leaf stem”, “Leaf hair”


  Feature Values or descriptors associated with features 


* ***V***  …or ***V\_{F}***     
  * feature values have significance only in the context of the specific features they relate to  
  * E.g. “entire” means something slightly di  
* Forms  
  * Categorical  
    * E.g. “Leaf shape”:   
  * Magnitude (integer or pair) \+ unit   
    * E.g.  5 \+ cm \- or 5 to 10 cm  
  * Binary: True/Fals {0,1}  
    * E.g. “leaf hair”

  Feature & Feature value sets, usually botanical or naturalist vocabularies include sets 

