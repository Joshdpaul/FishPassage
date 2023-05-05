"""A Python Fish Passage Model

This tool uses three functions to apply a proportional upstream passage model to a stream network with passage restrictions. It is designed to model fish passage over beaver dams, but could potentially be applied to other restrictions.

The stream network must have reaches with unique IDs, and a table that describes the relationship between a given reach and the reach immediately downstream (the "from-to" table). Passage restrictions must reference a reach ID, and reaches can have more than one passage restriction. Stream attributes used to split populations proportionally at confluences must be continuous values and must be available for all reaches in the network. To identify main stem reaches using this tool, the reaches must be grouped by tributaries or other meaningful hydrologic units. Alternatively, main stems can be defined outside of this tool using other stream attributes (eg, stream order, stream name) or manually in a GIS.     

This tool does not use or produce geospatial data (eg. shapefiles) but relies on tabular data derived from geospatial relationships. Spatial joins of stream networks, hydrologic units, and passage restrictions, and the creation of stream network "from-to" relationship tables, must be done before using this tool. 

This tool requires that `pandas` be installed within the Python environment. The 'sys' package is part of the Python standard library and should be included with any Python distribution. 

This tool should be imported as a module and contains the following functions:

    * find_main_stems : finds main stems in stream network
    * find_origins : finds origin reaches where fish exit main stems and start upstream into tributaries
    * fish_passage : models fish passage upstream from origins, identifying restrictions and calculating proportion of population passing
    
    ---------    
"""

import pandas
import sys


##### FIND MAIN STEMS FUNCTION

def find_main_stems(tr, ft):
    """Uses a collection of tributaries and the reaches therein to look for any reach within a tributary that flows "from" a reach outside of the tributary; those reaches are marked as being "non-terminal" (ie, the reach continues past the tributary boundary and into another one upstream). All non-terminal reaches are then propagated downstream until the opposite is true (ie, until we find a reach that flows "to" a reach outside of the tributary downstream). All reaches in between these two points are combined into a list of main stem reaches.
    
        If the stream network is not grouped by tributaries or other meaningful hydrologic units, consider defining the main stems list outside of this function using other stream attributes (eg, stream order, stream name) or manually in a GIS. 

    Parameters
    ----------
    tr : pandas dataframe, required
        A dataframe with tributary ID in the first column and unique reach ID in the second column. This table should represent one-to-many relationships between tributary polygons and the stream reaches within, and can be created using a spatial join method. If >2 columns, all columns after the first two will be ignored.
    ft : pandas dataframe, required
        A dataframe of "from-to" stream reach relationships, with unique reach ID in the first column ("flows from") and downstream unique reach ID in the second column ("flows to"). If >2 columns, all columns after the first two will be ignored.

    Returns
    -------
    list
        A list of unique reach IDs meeting the definition of a main stem (see above). Though many tributaries may be used in the input table, the output list is not specific to any one tributary and will contains all main stems.

    -------   
    """
    #check for errors in inputs, and exit with a message if errors found.
    print("Checking inputs...")
    
    if not isinstance(tr, pandas.DataFrame):
        sys.exit('Tributaries input must be pandas dataframe...check inputs')
    
    elif not isinstance(ft, pandas.DataFrame):
        sys.exit('From-to input must be pandas dataframe...check inputs')
        
    #make sure the input tables and lists are not empty
    elif (len(tr) == 0) or (len(ft) == 0):
        sys.exit('At least one input has length zero...check input tables and lists...check inputs')
    
    #if above conditions are not met (ie, no errors found and the script has not already exited), then start the model

    #seed an empty list for results
    all_main_stem_reaches = []
    
    #list all unique trib IDs in first column
    tribs = list(tr.iloc[:,0].unique())
    
    #count and provide message
    print('Processing ' + str(len(tribs)) + ' unique tributaries...')
        
    #loop thru trib IDs, creating a list with all corresponding reach IDs from the tributary table
    #seed an empty dataframe with from-to table columns, and populate with all from-to rows containing trib reaches
    #this will build a tributary-level subset of the from-to table
    for trib in tribs:
        reaches = list(tr[tr.iloc[:,0] == trib].iloc[:,1])
        
        ft_sub = pandas.DataFrame(columns=ft.columns.to_list())

        for r in reaches:
            rft = ft[ft.eq(r).any(axis=1)]
            ft_sub = pandas.concat([ft_sub, rft])   
    
        #if any of the from-to subset rows has a "from" ID that is NOT in the trib reach list, then its NOT a terminal stream
        #these are locations where the main stem reaches pass from one trib to the next in the upstream direction
        not_term_list = [i for i in ft_sub.iloc[:,0].to_list() if i not in reaches]
        
        #check to make sure there is something in the list before continuing
        if len(not_term_list) > 0:
            
            #seed an empty list for main stem reaches
            main_stem_reaches = []
            
            #starting at the non-terminal reach IDs, check all downstream IDs and add to the main stem reach list
            #unless finding a downstream ID not in the trib reach list (ie, passes from one trib to the next in the downstream direction)
            for n in not_term_list:
                main_stem_reaches.append(n)
                down = ft_sub[ft_sub.iloc[:, 0] == n].iloc[0, 1]
                
                if down in reaches:
                    not_term_list.append(down)
                else:
                    main_stem_reaches.append(down)
        
            #append all main stem reaches to the master results list            
            for m in main_stem_reaches:
                all_main_stem_reaches.append(m)
                
        else:
            #if not_term_list is length 0, just make an empty list
            all_main_stem_reaches = []
    
    #to remove any dupliates, only use unique values for the final list
    all_main_stem_reaches_unique = list(set(all_main_stem_reaches))
    
    #print a message 
    print('Found ' + str(len(all_main_stem_reaches_unique)) + ' unique main stem reaches.')
    
    return all_main_stem_reaches_unique


#####   FIND ORIGINS FUNCTION

def find_origins(ms, ft):
    """Uses a list of main stems (output from "find_main_stems" function, or user-defined by some other method) and a "from-to" dataframe to find locations where fish populations will theoretically move from a main stem into a tributary. These "origin" reaches are starting points from which fish passage modeling will proceed upstream. For each row in the "from-to" dataframe, the query looks for "from" reaches flowing "to" any of the reaches in the main stem list that are not themselves in the main stem list. If those conditions are met, the "from" reach is added to a list of origin reaches. 
    
    If the stream network is small, or more flexibility is needed, consider defining the origin list outside of this function using stream attributes (eg lowest elevation, highest flow) or manually in a GIS. 

    Parameters
    ----------
    ms : list, required
        A list of unique reach IDs meeting the definition of a main stem.
    ft : pandas dataframe, required
        A dataframe of "from-to" stream reach relationships, with unique reach ID in the first column ("flows from") and downstream unique reach ID in the second column ("flows to"). If >2 columns, all columns after the first two will be ignored.

    Returns
    -------
    list
        A list of unique reach IDs meeting the definition of an origin reach (see above).

    -------   
    """
    #check for errors in inputs, and exit with a message if errors found.
    print("Checking inputs...")
    
    if not isinstance(ft, pandas.DataFrame):
        sys.exit('From-To input must be pandas dataframe...check inputs')
    
    elif not isinstance(ms, list):
        sys.exit('Main stem input must be list...check inputs')
        
    #make sure the input tables and lists are not empty
    elif (len(ms) == 0) or (len(ft) == 0):
        sys.exit('At least one input has length zero...check input tables and lists...check inputs')
    
    #if above conditions are not met (ie, no errors found and the script has not already exited), then start the model

    #seed an empty list for origin reach IDs 
    origins = []

    #query each row in the from-to table, looking for reach IDs that flow "to" main stems, but are not main stems themselves
    #populate the origins list with any "from" reach IDs meeting that definition
    for row in range(len(ft)):
        r = ft.iloc[row]
        if r[1] in ms and r[0] not in ms:
            origins.append(r[0])
    
    #to remove any dupliates, only use unique values for the final list
    origins_unique = list(set(origins))
    
    #print a message
    print('Found ' + str(len(origins_unique)) + ' unique origin reaches flowing into main stems.')
    
    return origins_unique


#####   FISH PASSAGE FUNCTION

def fish_passage(dd, ori, ft, pct_pass, pct_cutoff, sa):
    """Takes a list of origin reaches where fish population will start upstream from the main stem (see "find_main_stems" and "find_origins" functions), and continues upstream using relationships in a "from-to" dataframe. At each reach, it's upstream "from" reach is queried in the dam dataframe. If dams are encountered, a reduction factor is applied to the remaining fish population in the reach. If there are multiple upstream reaches (ie, a confluence) the remaining fish population is split proportionally based on a stream attribute. The process continues upstream until the remaining fish population falls below the cutoff threshold, at which point iteration is stopped. The function can be limited to a specific habitat network by removing non-habitat reaches from the "from-to" dataframe. This effectively stops upstream travel at the first reach of unsuitable habitat, since there is no entry in the table for the next upstream reach. This function should work in complex networks (eg, 3-to-1 confluences, braided channels) but may result in multiple reach entries in the output dataframes. If using a braided stream network, it is recommended to check the output dataframes for duplicates, aggregate them, and apply a sum function.

    Parameters
    ----------
    dd : pandas dataframe, required
        A dataframe of reaches and their dams, with unique reach ID in the first column and Dam ID in the second column. Each dam should have a separate row. Dam ID does not have to be unique, as the script only counts number of rows to define number of dams. If >2 columns, all columns after the first two will be ignored.
    ori : list, required
        A list of unique reach IDs meeting the definition of an origin reach.
    ft : pandas dataframe, required
        A dataframe of "from-to" stream reach relationships, with unique reach ID in the first column ("flows from") and downstream unique reach ID in the second column ("flows to"). If >2 columns, all columns after the first two will be ignored.
    pct_pass : integer 0-100, required
        The percent of the reach population able to pass over a dam restriction.
    pct_cutoff : integer 1-100, required
        The percent population below which the model stops iterating upstream.
    sa : pandas dataframe OR str, required
        Option 1: If stream attributes are used to split the fish population, a dataframe with unique reach ID in the first column and the stream attribute in the second column. The attribute values are used to define the splitting proportion at confluences and must be a continuous value field (eg flow, width, depth, NOT a categorical field like stream order, stream name). If the population should be split evenly at confluences (not proportionally), simply use an attribute column with equal values for each reach. 
        Option 2: If fish population is not to be split at all, a string "NONE". This special case is designed to be useful when using the function as a shortcut to define the entire stream network (ie, use 100% passing, 1% cutoff, and "NONE" as stream attr input). If using this option to model fish passage, note that the entire population will be represented in each branch of the confluence; this will model the highest *potential* population in each branch, and may  actually make the sum of populations in each branch exceed 100%. 

    Returns
    -------
    list
        A list of dataframes, each dataframe corresponding to and named after a unique origin reach ID. Columns are unique origin reach ID and proportion of population remaining in the stream if greater than the threshold.

    -------   
    """
    #check for errors in inputs, and exit with a message if errors found.
    print("Checking inputs...")
    
    #make sure the stream attr input is a dataframe, and if its not, check if its a string "NONE"
    #if input is otherwise, exit with a message
    if isinstance(sa, pandas.DataFrame):
        print("Function will use stream attribute " + str(sa.columns.values[1]) + " to split population proportionally at confluences...")
        
    elif sa == 'NONE':
        print("Function will not split population proportionally at confluences...")
        
    else:
        sys.exit('Stream attribute input must be string "NONE" or a pandas dataframe...check inputs')
    
    
    #check the data types of remaining parameters
    if not isinstance(dd, pandas.DataFrame):
        sys.exit('Dams input must be pandas dataframe...check inputs')
    
    elif not isinstance(ft, pandas.DataFrame):
        sys.exit('From-To input must be pandas dataframe...check inputs')
        
    elif not isinstance(ori, list):
        sys.exit('Origins input must be list...check inputs')
    
    #make sure the input tables and lists are not empty
    elif (len(dd) == 0) or (len(ori) == 0) or (len(ft) == 0) or (len(sa) == 0):
        sys.exit('At least one input has length zero...check input tables and lists...check inputs')
        
    #make sure pct passing is between 0 and 100
    elif (pct_pass > 100) or (pct_pass < 0):
        sys.exit('Percent passing parameter must be an integer, with possible values of 0 to 100...check inputs')
        
    #make sure pct cutoff is between 1 and 100
    elif (pct_cutoff > 100) or (pct_cutoff < 1):
        sys.exit('Percent cutoff parameter must be an integer, with possible values of 1 to 100...check inputs') 
        
    #if above conditions are not met (ie, no errors found and the script has not already exited), then start the model
    
    #seed an empty list to hold resulting dictionaries
    o_dicts = []

    #loop thru origin list
    for origin in ori:
        #print a message
        print("Analyzing fish passage upstream of " + origin + ".......")

        #seed a starting population of 100
        #in the future, this number could be a function parameter and explicit origin stream population values could be used
        pop = 100

        #establish reduction factor (as decimal for multiplication)
        red = pct_pass/100

        #seed empty list of upstream IDs to iterate through, and immediately add the origin ID
        o_up_ids = []
        o_up_ids.append(origin)

        #seed empty dictionary to host results for this origin stream
        o_dict = {}

        #populate the dictionary key with the first origin stream, leaving the value (remaining population %) as null
        o_dict[origin] = None

        #if there are dams in the origin stream, count them and apply reduction factor; add reduced pop to dictionary
        if dd[dd.iloc[:,0] == origin].empty == False:

            dam_ct = len(dd[dd.iloc[:,0] == origin])
            red_pop = pop * (red ** dam_ct)
            o_dict[origin] = red_pop

        #if no dams found, use full starting population   
        else:
            o_dict[origin] = pop


        for o in o_up_ids:

            #look for the current reach ID as "to" in the from-to table, and return all the "from" values
            #these are reaches directly upstream of the current reach
            q = ft[ft.iloc[:,1] == o].iloc[:, 0]
            
            #we can now assess the upstream reaches for dams and apply passage reductions
            
            #if only one reach upstream (ie, there is no confluence)
            if (len(q) == 1):

                #append upstream reach to iteration list and create an dictionary key to hold population result computed below
                o_up_ids.append(q.iloc[0])
                o_dict[q.iloc[0]] = None

                #check for dams and if found, count them and apply reduction factor
                #if greater than cutoff, use reduced population as dictionary value from upstream key
                #if less than cutoff, remove upstream ID from list to stop iteration, and remove upstream key from dictionary as well
                #note: the ** operator is the exponent in python (usually written as ^)
                if dd[dd.iloc[:,0] == q.iloc[0]].empty == False:
                    dam_ct = len(dd[dd.iloc[:,0] == q.iloc[0]])
                    red_pop = o_dict[o] * (red ** dam_ct)
                    if red_pop > pct_cutoff:
                        o_dict[q.iloc[0]] = red_pop
                    else:
                        o_up_ids.remove(q.iloc[0])
                        del o_dict[q.iloc[0]]

                #if no dams found, use current population result as dictionary value for upstream key        
                else:
                    o_dict[q.iloc[0]] = o_dict[o]


            #if >1 reach upstream (ie, confluence)
            elif (len(q) > 1):

                #create empty lists to hold upstream reach ids and corresponding attribute values for each
                ids = []
                attrs = []
                
                #if a string was passed as an argument for 'sa' (ie, the "NONE" string checked above), then use 1 for all proportions
                #and populate the reach ids list
                if isinstance(sa, str) == True:

                    props = []

                    for a in range(len(q)):
                        props.append(1)
                        ids.append(q.iloc[a])

                #if a string was not passed, 'sa' will be a dataframe with stream attributes (checked above)
                #we can extract values from the second column to fill the attribute list
                #and populate the reach ids list
                else:
                    for a in range(len(q)):
                        attrs.append(sa[sa.iloc[:,0] == q.iloc[a]].iloc[:,1].values[0])
                        ids.append(q.iloc[a])

                    #convert attribute values to proportions
                    attr_sum = sum(attrs)
                    props = [val / attr_sum for val in attrs]

                #loop thru ids and their attr proportions
                for k, p in zip(ids, props):
                    
                    #append upstream reach to iteration list and create an dictionary key to hold population result computed below
                    o_up_ids.append(k)
                    o_dict[k] = None

                    #check for dams and if found, count them and apply reduction factor
                    #if greater than cutoff, use reduced population as dictionary value from upstream key
                    #note that in this case, the current population is reduced by multiplying by the corresponding proportion 'p'
                    #if less than cutoff, remove upstream ID from list to stop iteration, and remove upstream key from dictionary as well
                    #note: the ** operator is the exponent in python (usually written as ^)
                    if dd[dd.iloc[:,0] == k].empty == False:
                        dam_ct = len(dd[dd.iloc[:,0] == k])
                        red_pop = (o_dict[o] * p) * (red ** dam_ct)
                        if red_pop > pct_cutoff:
                            o_dict[k] = red_pop
                        else:
                            o_up_ids.remove(k)
                            del o_dict[k]

                    #if no dams found, use current population result as dictionary value for upstream key
                    #note that in this case, the current population is reduced by multiplying by the corresponding proportion 'p'
                    #if less than cutoff, remove upstream ID from list to stop iteration, and remove upstream key from dictionary as well
                    else:
                        red_pop = o_dict[o] * p
                        if red_pop > pct_cutoff:
                            o_dict[k] = red_pop
                        else:
                            o_up_ids.remove(k)
                            del o_dict[k]


            #if 0 reaches upstream (ie, no "from" reaches are found in the from-to table), do nothing        
            else:
                pass


        #append the result dictionary to master list of all dictionaries
        o_dicts.append(o_dict)
    
    #seed an empty list to hold result dataframes
    dfs = []

    #convert each dictionary to a dataframe and add to the df list
    #name the dataframe after the first row uID, which is the origin reach ID....this could be helpful in further iterations
    for od in o_dicts:
        df = pandas.DataFrame.from_dict(od, orient='index', columns=['pass']).reset_index(names='uID')
        df.name = df['uID'].iloc[0]
        dfs.append(df)    
        
    return dfs





