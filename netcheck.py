#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


#!/usr/bin/env python
import random
import logging
import itertools

logging.basicConfig()
logger = logging.getLogger()

class Vertex(object):
    def __init__(self, node, interface):
        self.node = node
        self.interface = interface
    def __str__(self):
        return "<Vtx: %s.%s>" % (self.node, self.interface)
    def __repr__(self):
        return self.__str__()
    def __eq__(self, other):
        return self.node == other.node and self.interface == other.interface
    def __ne__(self, other):
        return self.node != other.node or self.interface != other.interface
    def __hash__(self):
        return hash(str(self))


class Arc(object):
    def __init__(self, vertex_a, vertex_b):
        self.arc = (vertex_a, vertex_b)
    def __str__(self):
        return "<Arc: %s>" % (self.arc,)
    def __repr__(self):
        return self.__str__()
    def __getitem__(self, i):
        return self.arc[i]
    def __eq__(self, other):
        l = map(lambda x, y: x == y, self.arc, other.arc)
        return bool(filter(lambda x: x, l))
    def __ne__(self, other):
        l = map(lambda x, y: x != y, self.arc, other.arc)
        return bool(filter(lambda x: x, l))
    def __hash__(self):
        return hash(str(self))
    def invert(self):
        return Arc(self.arc[1], self.arc[0])


class NetChecker(object):
    def __init__(self, nodes, arcs):
        self.nodes = nodes
        self.arcs = arcs
        logger.debug("Init: got %d nodes and %d arcs", len(nodes), len(self.arcs))

    @staticmethod
    def _invert_arc(arc):
        return arc[1], arc[0]

    @staticmethod
    def _create_arc(a_vertex, b_vertex):
        return a_vertex, b_vertex

    @staticmethod
    def _disassm_vertex(vertex):
        index = vertex.find('.')
        node = vertex[:index]
        interface = vertex[index + 1:]
        return node, interface

    @staticmethod
    def _assm_vertex(node, interface):
        return "%s.%s" % (str(node), str(interface))

    def get_topos(self):
        """ Main method to collect all possible altermatives of
        interconnection.
        """
        topos = []
        vertices = set([i[0] for i in self.arcs])
        logger.debug("Get_choices: start with %d vertices", len(vertices))
        while vertices:
            logger.debug("")
            vertex = vertices.pop()
            logger.debug("Get_choices: entry vertex is %s", vertex)
            good_topos, visited_vertices = self._calc_topo(vertex)
            logger.debug("Get_choices: getted %d good_topos",
                         len(good_topos))
            logger.debug("Get_choices: getted %d visited_vertices: %s",
                         len(visited_vertices), visited_vertices)

            topos.extend(good_topos)
            vertices.difference_update(visited_vertices)
            logger.debug("Get_choices: %d untracked vertices left: %s",
                         len(vertices), vertices)
        return self._uniq_topos(topos)

    def _calc_topo(self, start_vertex):
        topos = []
        visited_vertices = set()

        def extend_arcs_to_check(arcs_to_check, arcs):
            for failed_v, ignored_v in arcs:
                existed_arcs = filter(
                    lambda x: x[0] == failed_v, arcs_to_check)
                if existed_arcs:
                    existed_arc = existed_arcs[0]
                    existed_arc[1].append(ignored_v)
                else:
                    arcs_to_check.append((failed_v, [ignored_v]))

        # arcs_to_check consists of arcs (x, y) where
        # x - failed vertex,
        # y - list of vertices which should be ignored.
        arcs_to_check = [(start_vertex, [])]
        for fv, ignored_vertices in arcs_to_check:
            found_vertices = [fv]
            failed_arcs = []

            for vertex in found_vertices:
                neighbors = self._get_neighbors(vertex)
                logger.debug("_calc_topo: for vtx %s a neigbors found: %s",
                             vertex, neighbors)
                new_vertices, absent_vertices = self._diff_lists(
                    found_vertices, ignored_vertices, neighbors
                )
                logger.debug("_calc_topo: new vtx found: %s", new_vertices)
                logger.debug("_calc_topo: absent_vertices is %s",
                             absent_vertices)
                if absent_vertices:
                    for v in absent_vertices:
                        failed_arc = (v, vertex)
                        if failed_arc not in failed_arcs:
                            failed_arcs.append(failed_arc)
                found_vertices.extend(new_vertices)

            failed_vertices = [x[0] for x in failed_arcs]
            topo = self._validate_topo(found_vertices, failed_vertices)
            visited_vertices.update(found_vertices)
            visited_vertices.update(failed_vertices)
            if topo:
                topos.append(topo)
            extend_arcs_to_check(arcs_to_check, failed_arcs)
        return topos, visited_vertices

    def _get_neighbors(self, vertex):
        arcs = filter(
            lambda x: x[0] == vertex,
            self.arcs)
        return [x[1] for x in arcs]

    @staticmethod
    def _diff_lists(found_vertices, ignored_vertices, neighbours):
        new_vertices = []
        absent_vertices = []
        for n in found_vertices:
            if n in neighbours:
                neighbours.remove(n)
            else:
                absent_vertices.append(n)
        new_vertices = [n for n in neighbours if n not in ignored_vertices]
        return new_vertices, absent_vertices

    def _validate_topo(self, found_v, failed_v):
        logger.debug("_validate_topo: found_vertices is: %s", found_v)
        logger.debug("_validate_topo: failed_vertices is: %s", failed_v)
        topo = {}
        for v in found_v:
            if v in failed_v:
                continue
            node, interface = self._disassm_vertex(v)
            interfaces = topo.get(node)
            if interfaces:
                interfaces.append(interface)
            else:
                topo[node] = [interface]
        if set(self.nodes) != set(topo.keys()):
            return None
        for l in topo.values():
            l.sort()
        return topo

    def _uniq_topos(self, topos):
        def isincluded(topo, topos):
            for at in topos:
                included = True
                for n in self.nodes:
                    if not set(topo[n]).issubset(set(at[n])):
                        included = False
                if included:
                    return True
            return False

        copy = []
        logger.debug("_uniq_topos: topos is %s" % topos)
        for t in topos:
            logger.debug("_uniq_topos: now testing: %s" % t)
            if not isincluded(t, [i for i in topos if id(i) != id(t)]):
                copy.append(t) 
        return copy


class ClassbasedNetChecker(NetChecker):
    @staticmethod
    def _invert_arc(arc):
        return arc.invert()

    @staticmethod
    def _create_arc(a_vertex, b_vertex):
        return Arc(a_vertex, b_vertex)

    @staticmethod
    def _disassm_vertex(vertex):
        return vertex.node, vertex.interface

    @staticmethod
    def _assm_vertex(node, interface):
        return Vertex(node, interface)





def generateFullMesh(nodes, interfaces, Klass, stability=1.0):
    A = []
    vertices = itertools.product(nodes, interfaces, nodes, interfaces)
    for n1, i1, n2, i2 in vertices:
        # Drop some arcs if stability < 1.0
        if stability == 1.0 or random.random() < stability:
            a_vertex = Klass._assm_vertex(n1, i1)
            b_vertex = Klass._assm_vertex(n2, i2)
            arc = Klass._create_arc(a_vertex, b_vertex)
            A.append(arc)
    logger.debug("generateArcs: %d arcs generated", len(A))
    return A

def generateMesh(nodes1, ifaces1, nodes2, ifaces2, Klass, stability=1.0):
    A = []
    vertices = itertools.product(nodes1, ifaces1, nodes2, ifaces2)
    for n1, i1, n2, i2 in vertices:
        # Drop some arcs if stability < 1.0
        if stability == 1.0 or random.random() < stability:
            a_vertex = Klass._assm_vertex(n1, i1)
            b_vertex = Klass._assm_vertex(n2, i2)
            arc = Klass._create_arc(a_vertex, b_vertex)
            A.append(arc)
    logger.debug("generateArcs: %d arcs generated", len(A))
    return A


def printChoice(choice, step=4):
    def printlist(l, indent=0, step=2):
        print '%s[' % (' ' * indent)        
        for i in l:
            if type(i) is dict:
                print '%s-' % (' ' * indent)
                printdict(i, indent + step, step)
            elif type(i) in (list, tuple):
                printlist(i, indent + step, step)
            else:
                print '%s- %s' % (' ' * indent, str(i))
        print '%s]' % (' ' * indent)                    
    def printdict(d, indent=0, step=2):
        for k, v in d.iteritems():
            if type(v) is dict:
                print '%s%s:' % (' ' * indent, str(k))
                printdict(v, indent + step, step)
            elif type(v) in (list, tuple):
                print '%s%s:' % (' ' * indent, str(k))
                printlist(v, indent + step, step)
            else:
                print '%s%s: %s' % (' ' * indent, str(k), str(v))
    if type(choice) is dict:
        printdict(choice, step=step)
    elif type(choice) is list:
        printlist(choice, step=step)
    else:
        print choice





print ""

nodes = ['s1', 's2', 's3', 's4']
interfaces = ['i0', 'i1', 'i2', 'i3']
logger.setLevel(logging.DEBUG)

Klass = ClassbasedNetChecker
Klass = NetChecker
arcs = []
# arcs.extend(generateFullMesh(nodes[:2], interfaces[:2], Klass, 0.9))
# #arcs.extend(generateFullMesh(nodes[:2], interfaces[2:], Klass))
# arcs.extend(generateMesh(nodes[2:3], interfaces[0:1],
#                          nodes[:3], interfaces[0:2], Klass))
# arcs.extend(generateMesh(nodes[:2], interfaces[0:2],
#                          nodes[2:3], interfaces[0:1], Klass))
# netcheck = Klass(nodes[:3], arcs)

nodes = [str(i) for i in xrange(200)]
interfaces = [str(i) for i in xrange(4)]
arcs = generateFullMesh(nodes, interfaces, Klass)
netcheck = Klass(nodes, arcs)
logger.setLevel(logging.INFO)
choices = netcheck.get_topos()

#printChoice(arcs)
# print ""
# for i in xrange(len(choices)):
#     print "\n---- Choice number %d: ----\n" % (i + 1)
#     printChoice(choices[i])
if not choices:
    print "No choices found"
else:
    print "%d choices found" % len(choices)
print ""

#import time
#time.sleep(5)
