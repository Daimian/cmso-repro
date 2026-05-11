import graphviz

d = graphviz.Digraph('dataflow', format='png', engine='dot')
d.attr(rankdir='TB', label='CMSO + atomRDF Data Flow: From Atomic Structure to Semantic Query',
       fontsize='18', labelloc='t', fontname='Helvetica-Bold',
       bgcolor='white', nodesep='0.6', ranksep='0.8', dpi='150', pad='0.5')

# ============================================================
# LAYER 1: Input Sources
# ============================================================
with d.subgraph(name='cluster_sources') as s:
    s.attr(label='Layer 1: Input Sources (Atomic Parameters / Simulation Output)',
           style='rounded,filled', fillcolor='#FEF9E7', color='#F39C12',
           fontname='Helvetica-Bold', fontsize='12', fontcolor='#7D6608')
    s.attr('node', shape='cylinder', style='filled', fontname='Helvetica', fontsize='10')
    s.node('bulk_in', 'Crystal Parameters\nFe/bcc, Cu/fcc,\nAl/fcc, Si/diamond',
           fillcolor='#F9E79F', color='#F39C12')
    s.node('defect_in', 'Defect Specs\nvacancy, substitutional,\ninterstitial',
           fillcolor='#F9E79F', color='#F39C12')
    s.node('mp_in', 'Materials Project\n(API JSON)',
           fillcolor='#F9E79F', color='#F39C12')
    s.node('lammps_in', 'LAMMPS / VASP\n(output files)',
           fillcolor='#F9E79F', color='#F39C12')
    s.node('pyiron_in', 'pyiron\n(job objects)',
           fillcolor='#F9E79F', color='#F39C12')

# ============================================================
# LAYER 2: atomRDF Python API (Mapping Layer)
# ============================================================
with d.subgraph(name='cluster_api') as s:
    s.attr(label='Layer 2: atomRDF Python API (Structure → RDF)',
           style='rounded,filled', fillcolor='#FDEBD0', color='#E67E22',
           fontname='Helvetica-Bold', fontsize='12', fontcolor='#784212')
    s.attr('node', shape='component', style='filled', fontname='Helvetica', fontsize='10')
    s.node('bulk_fn', 'atomrdf.build.bulk()\nase + spglib\n→ auto RDF',
           fillcolor='#FAD7A0', color='#E67E22')
    s.node('defect_fn', 'atomrdf.build.defect\n.vacancy() / .substitutional()\n.interstitial() / .dislocation()',
           fillcolor='#FAD7A0', color='#E67E22')
    s.node('parser_fn', 'WorkflowParser\nquery_mp()\nparse_job()',
           fillcolor='#FAD7A0', color='#E67E22')
    s.node('manual_fn', 'kg.graph.add()\nManual ASMO triples\n(method + property)',
           fillcolor='#FAD7A0', color='#E67E22')

    s.node('bridge', 'Auto-bridging:\nPython objects → ase.Atoms\n→ pyscal3 analysis\n→ RDF triples',
           shape='note', fillcolor='#FDEBD0', color='#E67E22', fontsize='9')

# ============================================================
# LAYER 3: TBox (5 Ontologies)
# ============================================================
with d.subgraph(name='cluster_tbox') as s:
    s.attr(label='Layer 3: TBox (OWL Ontology — 5 Modules, OCDO Suite)',
           style='rounded,filled', fillcolor='#D6EAF8', color='#2E86C1',
           fontname='Helvetica-Bold', fontsize='12', fontcolor='#1B4F72')
    s.attr('node', shape='box', style='filled,rounded', fontname='Helvetica', fontsize='10')
    s.node('cmso', 'CMSO\n\nAtomicScaleSample, Material,\nCrystalStructure, SpaceGroup,\nUnitCell, SimulationCell, Atom',
           fillcolor='#AED6F1', color='#2E86C1')
    s.node('asmo', 'ASMO\n\nDFT, EAM, kMC,\nFormationEnergy, BulkModulus,\nEnergyCutoff, KPointMesh',
           fillcolor='#FAD7A0', color='#E67E22')
    s.node('podo', 'PODO\n\nVacancy, Substitutional,\nInterstitial',
           fillcolor='#F8BBD0', color='#C62828')
    s.node('pldo', 'PLDO\n\nGrainBoundary,\nStackingFault, Dislocation',
           fillcolor='#A9DFBF', color='#28B463')
    s.node('ldo', 'LDO\n\nLineDefect, BurgersVector,\nSlipSystem, CharacterAngle',
           fillcolor='#D7BDE2', color='#8E44AD')

    # External vocabularies
    s.node('chebi', 'ChEBI\n(chemical elements)', shape='box', style='filled,rounded,dashed',
           fillcolor='#EAECEE', color='#717D7E', fontsize='9')
    s.node('wikidata', 'Wikidata\n(Bravais lattice)', shape='box', style='filled,rounded,dashed',
           fillcolor='#EAECEE', color='#717D7E', fontsize='9')
    s.node('qudt', 'QUDT\n(units: eV, Å³)', shape='box', style='filled,rounded,dashed',
           fillcolor='#EAECEE', color='#717D7E', fontsize='9')

    # Cross-ontology links
    s.edge('cmso', 'asmo', label='hasCalculatedProperty\nhasComputationalMethod',
           style='dotted', color='#2E86C1', fontsize='8', fontcolor='#2E86C1', arrowhead='vee')
    s.edge('cmso', 'podo', label='hasCrystallographicDefect',
           style='dotted', color='#C62828', fontsize='8', fontcolor='#C62828', arrowhead='vee')
    s.edge('cmso', 'pldo', label='hasCrystallographicDefect',
           style='dotted', color='#28B463', fontsize='8', fontcolor='#28B463', arrowhead='vee')
    s.edge('pldo', 'ldo', label='hasDislocation',
           style='dotted', color='#8E44AD', fontsize='8', fontcolor='#8E44AD', arrowhead='vee')

    s.edge('cmso', 'chebi', label='anchors elements', style='dotted', color='#717D7E',
           fontsize='8', fontcolor='#717D7E', arrowhead='vee')
    s.edge('cmso', 'wikidata', label='anchors lattice', style='dotted', color='#717D7E',
           fontsize='8', fontcolor='#717D7E', arrowhead='vee')
    s.edge('asmo', 'qudt', label='hasUnit', style='dotted', color='#717D7E',
           fontsize='8', fontcolor='#717D7E', arrowhead='vee')

# ============================================================
# LAYER 4: ABox (RDF Instance Data)
# ============================================================
with d.subgraph(name='cluster_abox') as s:
    s.attr(label='Layer 4: ABox (RDF Instance Data — KnowledgeGraph)',
           style='rounded,filled', fillcolor='#D5F5E3', color='#28B463',
           fontname='Helvetica-Bold', fontsize='12', fontcolor='#1D8348')
    s.attr('node', shape='box3d', style='filled', fontname='Helvetica', fontsize='10')
    s.node('kg', 'KnowledgeGraph\n(rdflib.Graph)\n\n~75 triples per bulk sample\n~79 triples per defect sample',
           fillcolor='#A9DFBF', color='#28B463')
    s.node('ttl', 'samples.ttl / full_kg.ttl\n(Turtle serialization)',
           fillcolor='#82E0AA', color='#1E8449')

# ============================================================
# LAYER 5: Query & Visualization
# ============================================================
with d.subgraph(name='cluster_query') as s:
    s.attr(label='Layer 5: Query & Visualization',
           style='rounded,filled', fillcolor='#E8DAEF', color='#8E44AD',
           fontname='Helvetica-Bold', fontsize='12', fontcolor='#4A235A')
    s.attr('node', shape='box', style='filled,rounded', fontname='Helvetica', fontsize='10')
    s.node('sparql', 'SPARQL Queries\nkg.query()\n4 CQ + custom cross-ontology',
           fillcolor='#D7BDE2', color='#8E44AD')
    s.node('t4rdf', 'tools4RDF\nDeclarative query\n(auto path-finding)',
           fillcolor='#D7BDE2', color='#8E44AD')
    s.node('viz', 'kg.visualise()\nGraphviz SVG',
           fillcolor='#D7BDE2', color='#8E44AD')
    s.node('results', 'Query Results\n\nCQ1: SpaceGroup per sample\nCQ2: bcc/fcc filter (drift!)\nCQ3: Volume range (drift!)\nCQ4: Atom count filter',
           shape='note', fillcolor='#F5EEF8', color='#8E44AD', fontsize='9')

# ============================================================
# EDGES: Data Flow
# ============================================================
edge_style = dict(penwidth='2.0', arrowhead='vee', arrowsize='0.8')

# Layer 1 → Layer 2
d.edge('bulk_in', 'bulk_fn', label='  element, crystal\n  structure, a  ', fontsize='9',
       color='#E67E22', fontcolor='#784212', **edge_style)
d.edge('defect_in', 'defect_fn', label='  type, count,\n  repeat  ', fontsize='9',
       color='#E67E22', fontcolor='#784212', **edge_style)
d.edge('mp_in', 'parser_fn', label='  API key  ', fontsize='9',
       color='#E67E22', fontcolor='#784212', **edge_style)
d.edge('lammps_in', 'parser_fn', label='  output path  ', fontsize='9',
       color='#E67E22', fontcolor='#784212', **edge_style)
d.edge('pyiron_in', 'parser_fn', fontsize='9', color='#E67E22', **edge_style)

# Bridge detail
d.edge('bulk_fn', 'bridge', style='dashed', color='#E67E22', arrowhead='none')

# Layer 2 → Layer 4 (API generates ABox)
d.edge('bulk_fn', 'kg', label='  75 triples / sample  ', fontsize='9',
       color='#28B463', fontcolor='#1D8348', **edge_style)
d.edge('defect_fn', 'kg', label='  + defect triples  ', fontsize='9',
       color='#28B463', fontcolor='#1D8348', **edge_style)
d.edge('parser_fn', 'kg', label='  parsed triples  ', fontsize='9',
       color='#28B463', fontcolor='#1D8348', **edge_style)
d.edge('manual_fn', 'kg', label='  ASMO triples  ', fontsize='9',
       color='#28B463', fontcolor='#1D8348', **edge_style)

# Layer 3 guides Layer 2 (TBox as template)
d.edge('cmso', 'bulk_fn', label='  defines classes\n  & properties  ', fontsize='8',
       color='#2E86C1', fontcolor='#1B4F72', style='dashed', arrowhead='vee')
d.edge('podo', 'defect_fn', label='  defect types  ', fontsize='8',
       color='#C62828', fontcolor='#C62828', style='dashed', arrowhead='vee')
d.edge('asmo', 'manual_fn', label='  method & property\n  vocabulary  ', fontsize='8',
       color='#E67E22', fontcolor='#784212', style='dashed', arrowhead='vee')

# Layer 4 internal
d.edge('kg', 'ttl', label='  serialize(format="turtle")  ', fontsize='9',
       color='#1E8449', fontcolor='#1D8348', **edge_style)

# Layer 4 → Layer 5
d.edge('kg', 'sparql', label='  kg.query(sparql_string)  ', fontsize='9',
       color='#8E44AD', fontcolor='#4A235A', **edge_style)
d.edge('kg', 't4rdf', label='  kg.query(ontology.terms...)  ', fontsize='9',
       color='#8E44AD', fontcolor='#4A235A', **edge_style)
d.edge('kg', 'viz', label='  kg.visualise()  ', fontsize='9',
       color='#8E44AD', fontcolor='#4A235A', **edge_style)
d.edge('sparql', 'results', color='#8E44AD', **edge_style)
d.edge('t4rdf', 'results', color='#8E44AD', **edge_style)

# ============================================================
# DRIFT annotation
# ============================================================
d.node('drift', '⚠ Documentation–Implementation Drift\n\n'
       '1. hasAltName: OWL defines it, atomRDF never emits it\n'
       '2. hasVolume: returns node, not literal (need asmo:hasValue)\n'
       '3. bulk() returns ase.Atoms, not (Atoms, Sample) tuple\n'
       '4. Namespace: cdos/cdco/ & cdos/podo/ vs cmso/ & podo/\n\n'
       '→ SPARQL must match ABox output, not OWL spec',
       shape='note', style='filled', fillcolor='#FDEDEC', color='#E74C3C',
       fontname='Helvetica', fontsize='9', fontcolor='#922B21')
d.edge('bulk_fn', 'drift', style='dashed', color='#E74C3C', arrowhead='none')
d.edge('drift', 'sparql', style='dashed', color='#E74C3C', arrowhead='none',
       label='  fix property names\n  & namespaces  ', fontsize='8', fontcolor='#922B21')

d.render('cmso_dataflow', cleanup=True)

from PIL import Image
img = Image.open('cmso_dataflow.png')
print(f'Generated: cmso_dataflow.png ({img.size[0]}x{img.size[1]})')

d.format = 'pdf'
d.render('cmso_dataflow', cleanup=True)
print('Generated: cmso_dataflow.pdf')
