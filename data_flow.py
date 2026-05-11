import graphviz

dot = graphviz.Digraph(
    "CMSO_atomRDF_DataFlow",
    format="svg",
    graph_attr={
        "rankdir": "TB",
        "fontname": "Helvetica",
        "fontsize": "14",
        "bgcolor": "white",
        "pad": "0.5",
        "nodesep": "0.6",
        "ranksep": "0.8",
        "label": "CMSO + atomRDF 数据流向图\n",
        "labelloc": "t",
        "fontsize": "20",
        "fontcolor": "#1a1a1a",
    },
    node_attr={
        "fontname": "Helvetica",
        "fontsize": "11",
        "style": "filled",
        "penwidth": "1.5",
    },
    edge_attr={
        "fontname": "Helvetica",
        "fontsize": "10",
        "color": "#666666",
        "penwidth": "1.2",
    },
)

# ── Layer 1: Input Sources ──
with dot.subgraph(name="cluster_input") as c:
    c.attr(label="① 数据输入源", style="dashed", color="#4A90D9", fontcolor="#4A90D9", fontsize="13")
    c.node("bulk_params",   "晶体参数\nFe/bcc/a=2.87\nCu/fcc/a=3.61 …",  shape="note",     fillcolor="#E3F2FD", color="#1565C0")
    c.node("defect_params", "缺陷参数\nvacancy / substitutional\ninterstitial",               shape="note",     fillcolor="#E3F2FD", color="#1565C0")
    c.node("asmo_params",   "计算参数\nDFT / EnergyCutoff\nFormationEnergy",                   shape="note",     fillcolor="#E3F2FD", color="#1565C0")
    c.node("ext_sources",   "外部数据源\nMaterials Project API\nLAMMPS / VASP 输出\npyiron job", shape="note",    fillcolor="#FFF9C4", color="#F9A825")

# ── Layer 2: atomRDF Python API ──
with dot.subgraph(name="cluster_atomrdf") as c:
    c.attr(label="② atomRDF Python API", style="dashed", color="#43A047", fontcolor="#43A047", fontsize="13")
    c.node("bulk_fn",    "bulk()\nase + spglib",         shape="box", fillcolor="#E8F5E9", color="#2E7D32")
    c.node("defect_fn",  "defect.vacancy()\n.substitutional()\n.interstitial()", shape="box", fillcolor="#E8F5E9", color="#2E7D32")
    c.node("manual_rdf", "手动添加\nkg.graph.add()",     shape="box", fillcolor="#E8F5E9", color="#2E7D32")
    c.node("parser_fn",  "WorkflowParser\nquery_mp()",   shape="box", fillcolor="#E8F5E9", color="#2E7D32")

# ── Layer 3: Intermediate Objects ──
with dot.subgraph(name="cluster_intermediate") as c:
    c.attr(label="③ 中间对象", style="dashed", color="#FF8F00", fontcolor="#FF8F00", fontsize="13")
    c.node("ase_atoms", "ase.Atoms\n原子坐标 + 晶格",   shape="ellipse", fillcolor="#FFF3E0", color="#E65100")
    c.node("sample_id", "Sample URI\nsample:UUID",       shape="ellipse", fillcolor="#FFF3E0", color="#E65100")

# ── Layer 4: KnowledgeGraph (core) ──
dot.node(
    "kg", "KnowledgeGraph\n(rdflib.Graph)",
    shape="cylinder", fillcolor="#F3E5F5", color="#6A1B9A",
    fontsize="13", penwidth="2.5", height="0.9",
)

# ── Layer 5: 5 Ontologies feeding into KG ──
with dot.subgraph(name="cluster_ontologies") as c:
    c.attr(label="④ 5 个本体 (语义模板)", style="dashed", color="#6A1B9A", fontcolor="#6A1B9A", fontsize="13")
    c.node("cmso_ont", "CMSO\n样本 / 晶体结构\nSpaceGroup / UnitCell",     shape="component", fillcolor="#EDE7F6", color="#4A148C")
    c.node("asmo_ont", "ASMO\n计算方法 / 属性\nDFT / FormationEnergy",     shape="component", fillcolor="#EDE7F6", color="#4A148C")
    c.node("podo_ont", "PODO\n点缺陷\nVacancy / Substitutional",          shape="component", fillcolor="#EDE7F6", color="#4A148C")
    c.node("pldo_ont", "PLDO\n面缺陷\nGrainBoundary / StackingFault",     shape="component", fillcolor="#EDE7F6", color="#4A148C")
    c.node("ldo_ont",  "LDO\n线缺陷\nDislocation / BurgersVector",        shape="component", fillcolor="#EDE7F6", color="#4A148C")

# ── Layer 6: External Anchors ──
with dot.subgraph(name="cluster_external") as c:
    c.attr(label="⑤ 外部锚定", style="dashed", color="#78909C", fontcolor="#78909C", fontsize="13")
    c.node("chebi",    "ChEBI\n化学元素",    shape="hexagon", fillcolor="#ECEFF1", color="#546E7A")
    c.node("wikidata", "Wikidata\n布拉维格子", shape="hexagon", fillcolor="#ECEFF1", color="#546E7A")
    c.node("qudt",     "QUDT\n单位 (eV, Å³)", shape="hexagon", fillcolor="#ECEFF1", color="#546E7A")

# ── Layer 7: Outputs ──
with dot.subgraph(name="cluster_output") as c:
    c.attr(label="⑥ 输出", style="dashed", color="#D32F2F", fontcolor="#D32F2F", fontsize="13")
    c.node("ttl",      "Turtle 文件\n.ttl",            shape="folder",    fillcolor="#FFEBEE", color="#B71C1C")
    c.node("sparql",   "SPARQL 查询\nCQ1–CQ4 + 自定义", shape="parallelogram", fillcolor="#FFEBEE", color="#B71C1C")
    c.node("svg",      "可视化\nSVG (graphviz)",       shape="folder",    fillcolor="#FFEBEE", color="#B71C1C")
    c.node("df",       "pandas DataFrame\n查询结果表格", shape="tab",       fillcolor="#FFEBEE", color="#B71C1C")

# ════════ Edges ════════

# Input → API
dot.edge("bulk_params",   "bulk_fn",    label="元素/晶系/\n晶格常数")
dot.edge("defect_params", "defect_fn",  label="缺陷类型/数量")
dot.edge("asmo_params",   "manual_rdf", label="方法/属性/值")
dot.edge("ext_sources",   "parser_fn",  label="API key /\n输出文件路径")

# API → Intermediate
dot.edge("bulk_fn",    "ase_atoms",  label="返回")
dot.edge("bulk_fn",    "sample_id",  label="注册到 KG", style="dashed")
dot.edge("defect_fn",  "ase_atoms",  label="返回")
dot.edge("defect_fn",  "sample_id",  label="注册到 KG", style="dashed")

# Intermediate + API → KG
dot.edge("ase_atoms",   "kg", label="坐标 → 三元组", color="#6A1B9A")
dot.edge("sample_id",   "kg", label="sample URI",     color="#6A1B9A")
dot.edge("manual_rdf",  "kg", label="ASMO 三元组",    color="#6A1B9A")
dot.edge("parser_fn",   "kg", label="解析 → 三元组",  color="#6A1B9A")

# Ontologies → KG (semantic templates)
for ont in ["cmso_ont", "asmo_ont", "podo_ont", "pldo_ont", "ldo_ont"]:
    dot.edge(ont, "kg", style="dotted", color="#9C27B0", arrowhead="empty", label="")

# External → KG
dot.edge("chebi",    "kg", style="dotted", color="#78909C", arrowhead="empty")
dot.edge("wikidata", "kg", style="dotted", color="#78909C", arrowhead="empty")
dot.edge("qudt",     "kg", style="dotted", color="#78909C", arrowhead="empty")

# KG → Outputs
dot.edge("kg", "ttl",    label="serialize()\nformat='turtle'", color="#D32F2F")
dot.edge("kg", "sparql", label="kg.query()",                   color="#D32F2F")
dot.edge("kg", "svg",    label="kg.visualise()\n+ graphviz",   color="#D32F2F")
dot.edge("sparql", "df", label="返回结果",                      color="#D32F2F")

dot.render("/Users/mian/workplace/cmso-repro/data_flow", cleanup=True)
print("Saved: data_flow.svg")
