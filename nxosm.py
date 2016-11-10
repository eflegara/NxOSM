#!/usr/bin/env python

"""
nxosm was written to extract and build a road network using OSM data;
to build adjacency matrix with geolocation information for each node.

Citation Format:
    Legara, E.F. (2014) nxosm source code (Version 2.0) [source code].
    http://www.erikalegara.net

"""

__author__ = "Erika Fille Legara"
__date__ = "22 January 2014"
__programname__ = "nxosm.py"
__codeversion__ = "2.0"
__status__ = "Complete"
__datasource__ = "http://labs.geofabrik.de/haiyan/"

from itertools import tee, izip
from osmread import parse_file, Way, Node #https://github.com/dezhin/osmread
# import shapefile
import networkx as nx

global highway_types
'''
For more highway types, visit http://wiki.openstreetmap.org/wiki/Key:highway
'''

highway_types = ['secondary', 'secondary_link', 'primary', 'primary_link',\
'tertiary', 'tertiary_link', 'motorway','motorway_link','trunk','trunk_link',\
'residential','road','track','Track']

def load_osm_pbf():
    return parse_file('latest.osm.pbf')

def load_osm(path):
    return parse_file(path)

# def load_intersection_nodes_file():
    # '''
    # The intersection file can be generated using QGIS.
    # '''
    # #shp = shapefile.Reader("small_set_intersection.shp")
    # shp = shapefile.Reader("For HaiyanPH Paper.shp")
    # shp_iter = shp.iterRecords()
    # return shp_iter

# def load_road_shapefile():
    # shp = shapefile.Reader("latest.shp/roads")
    # fields = shp.fields
    # return shp, fields

def pairwise(nodes):
    ''' From a list of nodes = [1,2,3,4,5],
    produce: (1,2), (2,3), (3,4), (4,5)'''
    a, b = tee(nodes)
    next(b, None)
    return izip(a,b)

def build_road_network(pbf):
    G = nx.Graph()
    node_locations = {}
    for entity in pbf:
        if isinstance(entity, Way) and 'highway' in entity.tags:
            if entity.tags['highway'] in highway_types:
                nodes = list(entity.nodes)
                edges = pairwise(nodes)
                edges = [e for e in edges]
                G.add_edges_from(edges)
                for e in edges:
                    G.edge[e[0]][e[1]]['tipo'] = entity.tags['highway']
        elif isinstance(entity,Node):
            node_locations[entity.id] = (entity.lon, entity.lat)
    return G, node_locations

def build_road_network_2(fil):
    G = nx.Graph()
    ndes = {}
    segments = []
    node_locations = {}
    for entity in fil:
        if isinstance (entity, Way) and 'highway' in entity.tags:
            #print "highway", entity.tags['highway']
            if entity.tags['highway'] in highway_types:
                nodes = list(entity.nodes)
                for n in nodes:
                    # Set flag that node n does belong to the road network
                    ndes[n]['way_part'] = True
                    
                edges = pairwise(nodes)
                edges = [e for e in edges]
                G.add_edges_from(edges)
                
                for e in edges:
                    segment = {}
                    segment['node_1'] = e[0]
                    segment['node_2'] = e[1]
                    segment['highway_type'] = entity.tags['highway']
                    segment['status'] = 'ok'
                    G.edge[e[0]][e[1]]['highway_type'] = entity.tags['highway']
                    G.edge[e[0]][e[1]]['status'] = 'ok'
                    # initialize road segment status tag such that we don't get a KeyError
                    if 'status' in entity.tags:
                        G.edge[e[0]][e[1]]['status'] = entity.tags['status']
                        segment['status'] = entity.tags['status']
                    segments.append(segment)
                    
                    
            
        elif isinstance(entity, Node):
            #print "Node!"
            #print entity.id. entity.lat, entity.lon
            node_locations[entity.id] = (entity.lat, entity.lon)
            #print node_locations[entity.id]
            nde = {}
            nde['nodeid'] = entity.id
            #print nde['nodeid'] 
            nde['latitude'] = entity.lat
            #print nde['latitude']
            nde['longitude'] = entity.lon
            #print nde['longitude']
            # Default node isn't a barrier so None. set otherwise
            nde['barrier'] = 'None'
            if 'barrier' in entity.tags:
                nde['barrier'] = entity.tags['barrier']
            #print nde['barrier']
            #print nde
            
            # Set flag that this node does not belong to the road network. 
            # Since in an OSM file nodes are listed ahead of ways, the way-handling code
            # above will set to true.
            nde['way_part'] = False
            ndes[entity.id] = nde # check for bug later
        
        # Before returning, remove all nodes in ndes which are not in G.
        # nodes_in_graph = [ndes[entry] for entry in G.nodes()]
        
    #return G, nodes_in_graph, node_locations, segments
    return G, ndes.values(), node_locations, segments
                
                
def get_nodes_locations(G):
    pbf = load_osm_pbf()
    nodes = G.nodes()
    node_attrib = {}
    for entity in pbf:
        if isinstance(entity, Node) and entity.id in nodes:

            node_attrib[entity.id] = (entity.lon, entity.lat)
    return node_attrib

def reduce_nodes(G):
    '''
    The reduce_nodes() function reduces the bigger and more complete
    graph G by identifying all nodes with degree 2 and removing them
    in the graph, and connecting their adjacent nodes to one another.
    '''
    g = G.copy()
    degree2 = []    #list of all nodes with degree 2

    for n in G.nodes():
        if G.degree(n) == 2:
            degree2.append(n)

    for v in degree2:
        edges = g.edges(v)
        try:
            first_edge = edges[0]
            last_edge = edges[-1]
            type1 = G[first_edge[1]][first_edge[0]]['tipo']
            type2 = G[last_edge[0]][last_edge[1]]['tipo']
            if type1 == type2:
                g.add_edge(first_edge[1],last_edge[1], tipo = type1)
                g.remove_edge(first_edge[0], first_edge[1])
                g.remove_edge(last_edge[0], last_edge[1])
        except:
            pass

    for v in degree2:
        if g.degree(v) == 0:
            g.remove_node(v)
    return g

if __name__ == "__main__":
    pbf = load_osm_pbf()
    G, node_locations = build_road_network(pbf)
    #shp = load_intersection_nodes_file()
    #node_attrib = get_nodes_locations(G)

    latlong_ids = {}
    for n in G.nodes():
        lat, lng = node_locations[n][1], node_locations[n][0]
        G.node[n]['latitude'] = node_locations[n][1]
        G.node[n]['longitude'] = node_locations[n][0]
        latlong_ids[(lat,lng)] = n

    '''
    The reduce_nodes() function reduces the bigger and more complete
    graph G by identifying all nodes with degree 2 and removing them
    in the graph, and connecting their adjacent nodes.
    '''
    #small_g = reduce_nodes(G)

    '''
    Here, we are writing out the network data structures to .gexf format.
    '''
    #nx.write_gexf(G,'road_network_all_nodes.gexf')
    #nx.write_gexf(small_g,'road_network_reduced.gexf')
    #np.save("all_nodes.npy",G.nodes())
