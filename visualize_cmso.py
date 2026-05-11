import rdflib
from rdflib.namespace import RDF, RDFS, OWL
import graphviz
import os

os.chdir('/Users/mian/workplace/cmso-repro')

g = rdflib.Graph()
for name in ['cmso', 'asmo', 'pldo', 'podo', 'ldo']:
    owl_files = [f for f in os.listdir(name) if f.endswith('.owl')]
    g.parse(f'{name}/{owl_files[0]}')

def short(uri):
    s = str(uri)
    for prefix, ns in [
        ('cmso:', 'http://purls.helmholtz-metadaten.de/cmso/'),
        ('asmo:', 'http://purls.helmholtz-metadaten.de/asmo/'),
        ('pldo:', 'http://purls.helmholtz-metadaten.de/pldo/'),
        ('pldo:', 'http://purls.helmholtz-metadaten.de/cdos/pldo/'),
        ('podo:', 'http://purls.helmholtz-metadaten.de/podo/'),
        ('podo:', 'http://purls.helmholtz-metadaten.de/cdos/podo/'),
        ('ldo:', 'http://purls.helmholtz-metadaten.de/ldo/'),
        ('cdco:', 'http://purls.helmholtz-metadaten.de/cdos/cdco/'),
        ('prov:', 'http://www.w3.org/ns/prov#'),
        ('qudt:', 'http://qudt.org/schema/qudt/'),
        ('owl:', 'http://www.w3.org/2002/07/owl#'),
        ('chebi:', 'http://purl.obolibrary.org/obo/'),
    ]:
        if s.startswith(ns):
            return prefix + s[len(ns):]
    return s.rsplit('/', 1)[-1].rsplit('#', 1)[-1]

def nid(uri):
    return str(uri).replace(':', '_').replace('/', '_').replace('#', '_').replace('.', '_')

def get_module(uri):
    s = str(uri)
    if '/cmso/' in s: return 'cmso'
    if '/asmo/' in s: return 'asmo'
    if '/pldo/' in s or 'cdos/pldo' in s: return 'pldo'
    if '/podo/' in s or 'cdos/podo' in s: return 'podo'
    if '/ldo/' in s: return 'ldo'
    if '/cdos/cdco/' in s: return 'cmso'
    if 'prov#' in s: return 'prov'
    if 'qudt' in s: return 'qudt'
    if 'chebi' in s or 'obo/' in s: return 'chebi'
    if 'wikidata' in s: return 'wikidata'
    return 'other'

FILL = {
    'cmso': '#D6EAF8', 'asmo': '#FDEBD0', 'pldo': '#D5F5E3',
    'podo': '#FCE4EC', 'ldo': '#E8DAEF',
    'prov': '#F5EEF8', 'qudt': '#EAECEE', 'chebi': '#FFF9C4',
    'wikidata': '#FFF9C4', 'other': '#F2F3F4',
}
BORDER = {
    'cmso': '#2E86C1', 'asmo': '#E67E22', 'pldo': '#28B463',
    'podo': '#C62828', 'ldo': '#8E44AD',
    'prov': '#A569BD', 'qudt': '#717D7E', 'chebi': '#F9A825',
    'wikidata': '#F9A825', 'other': '#ABB2B9',
}

all_classes = {c for c in g.subjects(RDF.type, OWL.Class) if isinstance(c, rdflib.URIRef)}
obj_props = {p for p in g.subjects(RDF.type, OWL.ObjectProperty) if isinstance(p, rdflib.URIRef)}
data_props = {p for p in g.subjects(RDF.type, OWL.DatatypeProperty) if isinstance(p, rdflib.URIRef)}

class_dps = {}
for dp in data_props:
    for dom in g.objects(dp, RDFS.domain):
        if isinstance(dom, rdflib.URIRef):
            class_dps.setdefault(dom, []).append(short(dp))

# ============================================================
# FIGURE 1: Class Hierarchy (all 5 ontologies)
# ============================================================
d1 = graphviz.Digraph('class_hierarchy', format='png', engine='dot')
d1.attr(rankdir='LR',
        label='CMSO Suite — Class Hierarchy (color = ontology, arrows = rdfs:subClassOf)',
        fontsize='22', labelloc='t', fontname='Helvetica-Bold',
        bgcolor='white', nodesep='0.25', ranksep='1.2',
        dpi='300', size='24,28')
d1.attr('node', shape='box', style='filled,rounded', fontname='Helvetica',
        fontsize='13', margin='0.15,0.08', height='0.3')
d1.attr('edge', arrowhead='empty', color='#666666', penwidth='1.2')

module_classes = {}
for c in all_classes:
    module_classes.setdefault(get_module(c), []).append(c)

MODULE_ORDER = ['cmso', 'asmo', 'pldo', 'podo', 'ldo']
counts = {m: len(module_classes.get(m, [])) for m in MODULE_ORDER}
MODULE_LABELS = {
    'cmso': f'CMSO — Computational Sample ({counts["cmso"]} classes)',
    'asmo': f'ASMO — Simulation Method & Property ({counts["asmo"]} classes)',
    'pldo': f'PLDO — Planar Defect ({counts["pldo"]} classes)',
    'podo': f'PODO — Point Defect ({counts["podo"]} classes)',
    'ldo': f'LDO — Line Defect ({counts["ldo"]} classes)',
}

for mod in MODULE_ORDER:
    classes = module_classes.get(mod, [])
    if not classes:
        continue
    with d1.subgraph(name=f'cluster_{mod}') as sg:
        sg.attr(label=MODULE_LABELS.get(mod, mod),
                style='rounded,filled',
                color=BORDER.get(mod, '#AAA'),
                fillcolor=FILL.get(mod, '#F8F8F8') + '30',
                fontname='Helvetica-Bold', fontsize='15',
                fontcolor=BORDER.get(mod, '#AAA'))
        for c in sorted(classes, key=lambda x: short(x)):
            sg.node(nid(c), label=short(c),
                    fillcolor=FILL.get(mod, '#F2F3F4'),
                    color=BORDER.get(mod, '#AAA'), penwidth='1.5')

for c in all_classes:
    for p in g.objects(c, RDFS.subClassOf):
        if isinstance(p, rdflib.URIRef) and p in all_classes:
            d1.edge(nid(c), nid(p))

with d1.subgraph(name='cluster_legend') as leg:
    leg.attr(label='Ontologies', style='dashed', color='gray', fontsize='14')
    for m in MODULE_ORDER:
        leg.node(f'leg_{m}', label=m.upper(), fillcolor=FILL[m], shape='box',
                 style='filled,rounded', fontsize='12',
                 color=BORDER[m])

d1.render('cmso_class_hierarchy', cleanup=True)
print('1/7 cmso_class_hierarchy.png')

d1.format = 'pdf'
d1.render('cmso_class_hierarchy', cleanup=True)
print('    cmso_class_hierarchy.pdf')

# ============================================================
# FIGURE 2: Object Property Map (Domain → Range)
# ============================================================
d2 = graphviz.Digraph('property_map', format='png')
d2.attr(rankdir='LR', label='CMSO Suite — Object Properties (Domain → Range)',
        fontsize='22', labelloc='t', fontname='Helvetica-Bold', bgcolor='white',
        nodesep='0.4', ranksep='1.2', dpi='300', size='24,20')
d2.attr('node', shape='box', style='filled,rounded', fontname='Helvetica', fontsize='13')

added = set()
for prop in obj_props:
    domains = [d for d in g.objects(prop, RDFS.domain) if isinstance(d, rdflib.URIRef)]
    ranges = [r for r in g.objects(prop, RDFS.range) if isinstance(r, rdflib.URIRef)]
    for d in domains:
        if nid(d) not in added:
            mod = get_module(d)
            d2.node(nid(d), label=short(d), fillcolor=FILL.get(mod, '#F2F3F4'),
                    color=BORDER.get(mod, '#BDC3C7'), penwidth='2')
            added.add(nid(d))
        for r in ranges:
            if nid(r) not in added:
                mod = get_module(r)
                d2.node(nid(r), label=short(r), fillcolor=FILL.get(mod, '#F2F3F4'),
                        color=BORDER.get(mod, '#BDC3C7'), penwidth='2')
                added.add(nid(r))
            mp = get_module(prop)
            d2.edge(nid(d), nid(r), label=short(prop), fontsize='11',
                    color=BORDER.get(mp, '#888'), fontcolor=BORDER.get(mp, '#888'))

d2.render('cmso_property_map', cleanup=True)
print('2/7 cmso_property_map.png')

# ============================================================
# FIGURE 3: Full OntoGraf-style (record nodes with datatype props)
# ============================================================
d3 = graphviz.Digraph('ontograf', format='png')
d3.attr(rankdir='LR', label='CMSO Suite — Full Ontology Graph', fontsize='24',
        labelloc='t', fontname='Helvetica-Bold', bgcolor='white',
        nodesep='0.5', ranksep='1.4', size='32,24', dpi='300')
d3.attr('node', shape='record', style='filled', fontname='Helvetica', fontsize='12')

for c in all_classes:
    mod = get_module(c)
    label = short(c)
    dps = class_dps.get(c, [])
    if dps:
        dp_str = '\\l'.join(sorted(dps)) + '\\l'
        label = f'{{{label}|{dp_str}}}'
    else:
        label = f'{{{label}}}'
    d3.node(nid(c), label=label, fillcolor=FILL.get(mod, '#F2F3F4'),
            color=BORDER.get(mod, '#BDC3C7'), penwidth='2')

for c in all_classes:
    for p in g.objects(c, RDFS.subClassOf):
        if isinstance(p, rdflib.URIRef) and p in all_classes:
            d3.edge(nid(c), nid(p), arrowhead='empty', color='#333', penwidth='1.5')

for prop in obj_props:
    domains = [d for d in g.objects(prop, RDFS.domain) if isinstance(d, rdflib.URIRef)]
    ranges = [r for r in g.objects(prop, RDFS.range) if isinstance(r, rdflib.URIRef)]
    for d in domains:
        for r in ranges:
            mp = get_module(prop)
            d3.edge(nid(d), nid(r), label=short(prop), fontsize='10',
                    color=BORDER.get(mp, '#888'), fontcolor=BORDER.get(mp, '#888'),
                    style='dashed', arrowhead='vee')

d3.render('cmso_ontograf', cleanup=True)
print('3/7 cmso_ontograf.png')

# ============================================================
# FIGURES 4-8: Per-ontology module diagrams
# ============================================================
for mod_name in MODULE_ORDER:
    owl_files = [f for f in os.listdir(mod_name) if f.endswith('.owl')]
    mg = rdflib.Graph()
    mg.parse(f'{mod_name}/{owl_files[0]}')

    dot = graphviz.Digraph(f'module_{mod_name}', format='png')
    dot.attr(rankdir='TB', label=f'OCDO Module: {mod_name.upper()}', fontsize='20',
             labelloc='t', fontname='Helvetica-Bold', bgcolor='white',
             dpi='300', nodesep='0.5', ranksep='0.9')
    dot.attr('node', shape='record', style='filled', fontname='Helvetica', fontsize='13',
             fillcolor=FILL.get(mod_name, '#F2F3F4'),
             color=BORDER.get(mod_name, '#BDC3C7'), penwidth='2')

    mc = {c for c in mg.subjects(RDF.type, OWL.Class) if isinstance(c, rdflib.URIRef)}

    mdp = {}
    for dp in mg.subjects(RDF.type, OWL.DatatypeProperty):
        if isinstance(dp, rdflib.URIRef):
            for dom in mg.objects(dp, RDFS.domain):
                if isinstance(dom, rdflib.URIRef):
                    mdp.setdefault(dom, []).append(short(dp))

    ext_added = set()
    for c in mc:
        label = short(c)
        dps = mdp.get(c, [])
        if dps:
            dp_str = '\\l'.join(sorted(dps)) + '\\l'
            label = f'{{{label}|{dp_str}}}'
        else:
            label = f'{{{label}}}'
        dot.node(nid(c), label=label)

    for c in mc:
        for p in mg.objects(c, RDFS.subClassOf):
            if isinstance(p, rdflib.URIRef):
                if p not in mc and nid(p) not in ext_added:
                    ext_mod = get_module(p)
                    dot.node(nid(p), label=short(p),
                             fillcolor=FILL.get(ext_mod, '#EAECEE'),
                             color=BORDER.get(ext_mod, '#85929E'))
                    ext_added.add(nid(p))
                if p in mc or nid(p) in ext_added:
                    dot.edge(nid(c), nid(p), arrowhead='empty', color='#333', penwidth='1.5')

    for prop in mg.subjects(RDF.type, OWL.ObjectProperty):
        if not isinstance(prop, rdflib.URIRef):
            continue
        domains = [d for d in mg.objects(prop, RDFS.domain) if isinstance(d, rdflib.URIRef)]
        ranges = [r for r in mg.objects(prop, RDFS.range) if isinstance(r, rdflib.URIRef)]
        for d in domains:
            for r in ranges:
                if d not in mc and nid(d) not in ext_added:
                    ext_mod = get_module(d)
                    dot.node(nid(d), label=short(d),
                             fillcolor=FILL.get(ext_mod, '#EAECEE'),
                             color=BORDER.get(ext_mod, '#85929E'))
                    ext_added.add(nid(d))
                if r not in mc and nid(r) not in ext_added:
                    ext_mod = get_module(r)
                    dot.node(nid(r), label=short(r),
                             fillcolor=FILL.get(ext_mod, '#EAECEE'),
                             color=BORDER.get(ext_mod, '#85929E'))
                    ext_added.add(nid(r))
                dot.edge(nid(d), nid(r), label=short(prop), fontsize='10', style='dashed',
                         color=BORDER.get(mod_name, '#888'),
                         fontcolor=BORDER.get(mod_name, '#888'))

    n = MODULE_ORDER.index(mod_name) + 4
    dot.render(f'cmso_module_{mod_name}', cleanup=True)
    print(f'{n}/7 cmso_module_{mod_name}.png')

print('\nAll 8 ontology visualizations generated!')
