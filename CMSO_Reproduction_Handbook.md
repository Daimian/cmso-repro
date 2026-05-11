# CMSO + atomRDF 复现操作手册

**复现对象:** Computational Material Sample Ontology (CMSO) 及其姊妹本体 ASMO/PLDO/PODO,以及生成 RDF 知识图谱的 Python 库 atomRDF。

**与 MDO 复现的本质区别**

| 维度 | MDO 复现 | CMSO 复现 |
|---|---|---|
| 入口方式 | 手写 SPARQL + JSON 映射规则 | 用 Python 库 (atomRDF) **自动生成** RDF |
| 数据源 | Materials Project JSON dump | 直接生成 bulk crystal / 解析 LAMMPS / VASP 输出 |
| 工作量重点 | 理解 OWL 模块化设计 | 理解从计算原子结构到 RDF 的"自动桥接"机制 |
| 学到什么 | 经典本体工程 | "本体即代码"的现代实践 |
| 代码量 | 多写 SPARQL,少写 Python | 多写 Python,SPARQL 在库里自动生成 |

**这个仓库适合复现的两个理由:**
1. **atomRDF 不仅是一个本体,它是一整套"计算 → RDF"的可执行工具链**,这种"alive ontology"的工程范式正是磁性计算领域稀缺的
2. **CMSO + ASMO + PLDO + PODO 的多本体协同**示范了如何把"样本/方法/线缺陷/点缺陷"四类问题正交分解——直接可借鉴到 mag-material-ontology

**预期总耗时:** 10–13 小时分布在 2–3 周

**前置技能:** Python 基础、对原子结构有概念、Jupyter 用过

**软件需求:** Python 3.9+,Graphviz(可视化用),conda 或 venv

---

## 总览

| 阶段 | 内容 | 时长 |
|---|---|---|
| **阶段 0** | 环境与本体仓库 | 0.5 h |
| **阶段 1** | 阅读 5 个本体(CMSO/ASMO/PLDO/PODO/LDO)的设计 | 2 h |
| **阶段 2** | atomRDF 入门:构建第一个 RDF 知识图谱 | 1.5 h |
| **阶段 3** | 跑通 4 个官方 CQ + 处理 documentation drift | 2 h |
| **阶段 4** | 缺陷:用 PODO 生成空位/置换/间隙 + PLDO 生成位错 | 2 h |
| **阶段 5** | ASMO:把"计算方法 + 计算属性"加进 KG | 1.5 h |
| **阶段 6** | Materials Project 集成 + Workflow Parser | 1.5 h |
| **阶段 7** | 可视化 + 持久化 + 复现报告 | 1 h |

---

## 阶段 0 — 环境搭建 (30 分钟)

### 0.1 操作系统与 Python

```bash
# Linux/macOS 推荐
python3 --version       # 应 ≥ 3.9
```

### 0.2 创建工作目录与虚拟环境

```bash
mkdir -p ~/cmso-repro && cd ~/cmso-repro
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### 0.3 安装 atomRDF(关键工具)

```bash
pip install atomrdf
```

这一条命令会自动装上 60+ 个依赖包,包括:
- `rdflib` (RDF 解析)
- `pyscal3` + `ase` (原子结构操作)
- `spglib` (空间群识别)
- `pymatgen` (Materials Project 接入,可选)
- `tools4RDF` (SPARQL 自动生成)
- `graphviz` (可视化)

> **可能踩的坑:** Ubuntu 24 之后系统 Python 是 PEP 668 保护的,装包要加 `--break-system-packages`,**但应优先使用 venv 来避免这个问题**。

### 0.4 验证安装

```bash
python3 -c "
from atomrdf import KnowledgeGraph
from atomrdf.build import bulk
kg = KnowledgeGraph()
bulk('Fe', crystalstructure='bcc', a=2.87, cubic=True, graph=kg)
print(f'OK: {len(kg.graph)} triples generated')
"
```

**预期输出:** `OK: 75 triples generated`

### 0.5 Clone 五个本体仓库

```bash
cd ~/cmso-repro
for ont in cmso-ontology asmo pldo podo ldo; do
    git clone --depth 1 https://github.com/OCDO/$ont.git
done
mv cmso-ontology cmso
ls
```

应该看到 `cmso/  asmo/  pldo/  podo/  ldo/`。每个目录里都有一个 `.owl` 文件。

### 0.6 装 Graphviz 系统包(给可视化用)

```bash
# Ubuntu/Debian
sudo apt install graphviz
# macOS
brew install graphviz
```

### 阶段 0 验收

执行下面命令,显示所有 5 个本体的规模:

```python
import rdflib
from rdflib.namespace import RDF, OWL

for name in ['cmso', 'asmo', 'pldo', 'podo', 'ldo']:
    g = rdflib.Graph()
    g.parse(f'{name}/{name}.owl')
    n_classes = sum(1 for _ in g.subjects(RDF.type, OWL.Class))
    print(f"{name.upper():6s}: {len(g):5d} triples, {n_classes} classes")
```

**预期输出**(以 2026-05 仓库版本为准):
```
CMSO  : 600  triples, 45 classes
ASMO  : 1161 triples, 105 classes
PLDO  : 352  triples, 29 classes
PODO  : 208  triples, 12 classes
LDO   : 208  triples, 29 classes
```

---

## 阶段 1 — 理解 5 个本体的协同设计 (2 小时)

CMSO 不是单打独斗——它和 4 个姊妹本体一起构成 OCDO suite。你必须先理解每个本体**负责什么**,才能理解 atomRDF 为什么这么写。

### 1.1 看图:5 个本体的职责分工

```
┌─────────────────────────────────────────────────────────────┐
│                       OCDO Suite                             │
├─────────────────────────────────────────────────────────────┤
│  CMSO  ── 计算样本/晶体结构      (用来描述"算什么")           │
│   ├── CrystallineMaterial                                    │
│   ├── AtomicScaleSample (核心类)                             │
│   ├── UnitCell, SimulationCell, Atom, Basis                  │
│   └── SpaceGroup                                             │
│                                                              │
│  ASMO  ── 仿真方法 + 计算属性    (用来描述"怎么算的、算出了啥") │
│   ├── DensityFunctionalTheory, AbInitioMolecularDynamics    │
│   ├── InteratomicPotential, EmbeddedAtomModel               │
│   ├── EnergyCalculation, FreeEnergyCalculation              │
│   ├── ElasticConstant, FormationEnergy, BulkModulus         │
│   └── InputParameter (KPointMesh, EnergyCutoff, ...)        │
│                                                              │
│  PLDO  ── 平面缺陷            (位错、晶界、堆垛层错)         │
│   ├── GrainBoundary, StackingFault                          │
│   └── Dislocation                                            │
│                                                              │
│  PODO  ── 点缺陷              (空位、间隙、置换)             │
│   ├── Vacancy, Interstitial, Substitutional                 │
│   └── (用 hasVacancyConcentration 等属性)                    │
│                                                              │
│  LDO   ── 线缺陷              (位错的精细描述)              │
│   └── (Dislocation 子类型,Burgers vector 等)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │     atomRDF      │
                  │  Python library  │
                  └──────────────────┘
                            │
                            ▼
            生成符合上述 5 个本体的 RDF 知识图谱
```

### 1.2 实操:列出每个本体的核心类

新建 `~/cmso-repro/explore_ontologies.py`:

```python
import rdflib
from rdflib.namespace import RDF, RDFS, OWL

for name in ['cmso', 'asmo', 'pldo', 'podo', 'ldo']:
    g = rdflib.Graph()
    g.parse(f'{name}/{name}.owl')
    
    print(f"\n========== {name.upper()} ==========")
    
    classes = [s for s in g.subjects(RDF.type, OWL.Class) 
               if isinstance(s, rdflib.URIRef) and name in str(s).lower()]
    
    print(f"Triples: {len(g)},  classes: {len(classes)}")
    
    # 列出顶层类(没有 cmso/asmo 父类的类)
    print("Top-level classes:")
    for c in sorted(classes):
        c_name = str(c).rsplit('/', 1)[-1].rsplit('#', 1)[-1]
        parents_in_ns = [p for p in g.objects(c, RDFS.subClassOf)
                          if isinstance(p, rdflib.URIRef) and name in str(p).lower()]
        if not parents_in_ns:
            print(f"   {c_name}")
```

```bash
python3 explore_ontologies.py
```

### 1.3 重点理解 CMSO 的 ComputationalSample 层级

这是 CMSO 最有借鉴价值的设计——**计算样本按尺度分类**:

```
ComputationalSample
   ├── AtomicScaleSample     (DFT, classical MD, ab initio MD)
   ├── NanoscaleSample       (中尺度,例如 coarse-grained MD)
   ├── MesoscaleSample       (例如位错动力学)
   ├── MicroscaleSample      (例如相场)
   └── MacroscaleSample      (例如有限元)
```

**为什么这个分类对你有启示**:磁性领域的多尺度也是同构的:
- AtomicScaleSample → spin model on lattice (Heisenberg/Stoner)
- MesoscaleSample → atomistic spin dynamics (UppASD)
- MicroscaleSample → micromagnetic (LLG/Ubermag/MuMax)
- MacroscaleSample → bulk magnetic device simulation

### 1.4 阅读 4 个官方 CQ

```bash
cat cmso/requirements/README.md
```

把 4 个 CQ 用自己的话翻译一遍:
- **CQ1** = 找出 N 原子的样本的空间群
- **CQ2** = 找 BCC/FCC 晶体结构的样本
- **CQ3** = 体积在某范围的模拟元胞
- **CQ4** = 含 N 原子的超胞样本

> **注意:** CMSO 官方仓库只列了 4 个 CQ。如果你想看大规模真实用例,看 Guzmán 等 2026 年 arXiv:2604.06230(750K triples 的生产级 demo)。

### 1.5 PROV-O 在哪里?

CMSO **不直接 import PROV-O**(检查 `imports` 是空的就知道),但 ASMO 在描述 calculation provenance 时会用到 PROV-O 概念。这是它"模块化"的代价——**不强行 import 任何上层本体**,让用户按需组合。

### 阶段 1 验收

能回答这三个问题:
1. CMSO 和 ASMO 的边界在哪里?(一个描述"样本",一个描述"用什么方法算 + 算出了什么"。CMSO 的 AtomicScaleSample 通过 `asmo:hasCalculatedProperty` 链到 ASMO 的属性)
2. 为什么 PODO 只有 12 个类却独立成本体?(因为点缺陷描述有强烈的"组合性"——一个空位可以和置换共存,所以单独成体)
3. CMSO **没有** import 任何上层本体,这是优势还是劣势?(优势:任何人可用;劣势:跨领域语义对齐要自己做)

---

## 阶段 2 — atomRDF 入门:从原子到 RDF (1.5 小时)

### 2.1 你的第一个 RDF 三元组

新建 `~/cmso-repro/first_kg.py`:

```python
from atomrdf import KnowledgeGraph
from atomrdf.build import bulk

# 创建空知识图谱
kg = KnowledgeGraph()

# 用 ase + spglib 生成一个 BCC Fe 单胞,自动转 RDF
atoms = bulk("Fe", crystalstructure="bcc", a=2.87, cubic=True, graph=kg)

print(f"Atoms: {len(atoms)}")
print(f"Triples in KG: {len(kg.graph)}")
print(f"Samples registered: {kg.n_samples}")

# 看看三元组长什么样
for s, p, o in list(kg.graph)[:10]:
    s_short = str(s).rsplit('/', 1)[-1].rsplit('#', 1)[-1][:50]
    p_short = str(p).rsplit('/', 1)[-1].rsplit('#', 1)[-1][:30]
    o_short = str(o).rsplit('/', 1)[-1].rsplit('#', 1)[-1][:50]
    print(f"  {s_short:50s}  --{p_short:30s}-->  {o_short}")
```

**预期输出:**
```
Atoms: 2
Triples in KG: 75
Samples registered: 1
```

### 2.2 ⚠ 关键 API 提示

`bulk()` 的 help 文档说返回 `(Atoms, AtomicScaleSample)` 元组,但**实测在当前版本它只返回 ase.Atoms 对象**。Sample 对象通过 `kg.sample_ids` 访问。这是 documentation drift,记下来。

```python
sample_id = kg.sample_ids[0]   # 这才是 sample URI
print(f"Sample URI: {sample_id}")   # sample:abc-def-...
```

### 2.3 atomRDF 自动生成了哪些三元组

每个 bulk 调用生成的 ~75 个三元组覆盖:

| 类别 | 实例 | CMSO 类 |
|---|---|---|
| 样本本身 | `sample:UUID` | `AtomicScaleSample` |
| 化学组成 | `_ChemicalSpecies` | `ChemicalSpecies` |
| 化学元素 | 链到 `CHEBI:18248` (Fe) | `ChemicalElement` (用 ChEBI) |
| 晶体结构 | `_CrystalStructure` | `CrystalStructure` |
| 空间群 | `Im-3m`, number 229 | `SpaceGroup` |
| 布拉维格子 | 链到 Wikidata `Q851536` (cubic) | `BravaisLattice` |
| 单胞 | 长度/角度 | `UnitCell` |
| 模拟元胞 | 9 维向量、体积 | `SimulationCell` |
| 原子属性 | Position, Species | `AtomAttribute` |

**关键设计模式:外部本体对齐**——元素用 ChEBI,布拉维格子用 Wikidata,这是 OCDO 文档里说的"upper-ontology-agnostic + external anchoring"策略。

### 2.4 构建多个样本

```python
from atomrdf import KnowledgeGraph
from atomrdf.build import bulk

kg = KnowledgeGraph()
bulk("Fe", crystalstructure="bcc", a=2.87, cubic=True, graph=kg)
bulk("Cu", crystalstructure="fcc", a=3.61, cubic=True, graph=kg)
bulk("Al", crystalstructure="fcc", a=4.05, cubic=True, graph=kg)
bulk("Si", crystalstructure="diamond", a=5.43, cubic=True, graph=kg)

print(f"Built {kg.n_samples} samples in {len(kg.graph)} triples")
# 预期: 4 samples in ~300 triples
```

### 2.5 持久化:导出/重载 RDF

```python
# 写到 turtle 文件
ttl_str = kg.graph.serialize(format='turtle')
with open('my_samples.ttl', 'w') as f:
    f.write(ttl_str)

# 重载
import rdflib
g2 = rdflib.Graph()
g2.parse('my_samples.ttl', format='turtle')
print(f"Reloaded {len(g2)} triples")
```

> **注意:** `kg.to_file()` 这个方法**不是用来存 RDF 的**,它是用来把样本导出为 LAMMPS data 或 VASP POSCAR 这类**材料模拟输入文件**的。这是另一个容易踩的坑。

### 阶段 2 验收

写一个脚本 `multi_samples.py`,生成 5 种不同材料的样本,保存到 `samples.ttl`,然后用 rdflib 重载并打印总三元组数。

---

## 阶段 3 — 跑通 4 个官方 CQ 并处理"documentation drift" (2 小时)

这是整个复现里**最有学术价值的部分**——发现并记录官方 CQ 文档与实际 atomRDF 输出的不一致,作为你复现报告的核心贡献。

### 3.1 准备测试数据

```python
from atomrdf import KnowledgeGraph
from atomrdf.build import bulk

kg = KnowledgeGraph()
bulk("Fe", crystalstructure="bcc", a=2.87, cubic=True, graph=kg)        # 2 atoms
bulk("Cu", crystalstructure="fcc", a=3.61, cubic=True, graph=kg)        # 4 atoms
bulk("Al", crystalstructure="fcc", a=4.05, cubic=True, graph=kg)        # 4 atoms
bulk("Si", crystalstructure="diamond", a=5.43, cubic=True, graph=kg)    # 8 atoms

print(f"KG: {len(kg.graph)} triples, {kg.n_samples} samples")
```

### 3.2 CQ1:跑通(没问题)

```python
q1 = """
PREFIX cmso: <http://purls.helmholtz-metadaten.de/cmso/>
SELECT ?sample ?natoms ?symbol
WHERE {
    ?sample cmso:hasNumberOfAtoms ?natoms .
    ?sample cmso:hasMaterial ?material .
    ?material cmso:hasStructure ?structure .
    ?structure cmso:hasSpaceGroupSymbol ?symbol .
}"""

df = kg.query(q1)
print(df)
```

**预期输出**(pandas DataFrame):
```
                            sample  natoms  symbol
0   sample:xxx-Fe                    2       Im-3m
1   sample:yyy-Cu                    4       Fm-3m
2   sample:zzz-Al                    4       Fm-3m
3   sample:www-Si                    8       Fd-3m
```

### 3.3 CQ2:**第一个 drift!** `hasAltName` 不存在

按 README 原样跑:

```python
q2 = """
PREFIX cmso: <http://purls.helmholtz-metadaten.de/cmso/>
SELECT DISTINCT ?sample ?altname
WHERE {     
    ?sample cmso:hasMaterial ?material .     
    ?material cmso:hasStructure ?crystalstructure .     
    ?crystalstructure cmso:hasAltName ?altname . 
    FILTER (?altname="bcc" || ?altname="fcc")
}"""
df = kg.query(q2)
print(df)
```

**结果:空** ❌

**调查:** 列出所有谓词,找有没有类似 "altname" 的:

```python
preds = set(str(p).rsplit('/', 1)[-1] for s, p, o in kg.graph)
print(sorted(preds))
```

会发现 atomRDF 实际**没有发出 `hasAltName` 三元组**。它存了空间群符号(Im-3m / Fm-3m / Fd-3m)但没存 "bcc" / "fcc" 的 alt name。

**两种修复:**

(a) 改用空间群+atom数判别(可信但 SPARQL 复杂):
```python
# bcc = SG 229 with 2 atoms in unit cell
# fcc = SG 225 with 4 atoms in unit cell
q2_fixed = """
PREFIX cmso: <http://purls.helmholtz-metadaten.de/cmso/>
SELECT DISTINCT ?sample
WHERE {     
    ?sample cmso:hasNumberOfAtoms ?n .
    ?sample cmso:hasMaterial ?m .
    ?m cmso:hasStructure ?cs .
    ?cs cmso:hasSpaceGroupSymbol ?sg .
    FILTER ( (?sg = "Im-3m" && ?n = 2) || (?sg = "Fm-3m" && ?n = 4) )
}"""
```

(b) 给 KG 手动加 `hasAltName` 三元组(更尊重原 CQ):
```python
from rdflib import Namespace, Literal, URIRef
CMSO = Namespace("http://purls.helmholtz-metadaten.de/cmso/")

# 给每个 sample 的 CrystalStructure 加上 altname
for s, p, o in list(kg.graph.triples((None, CMSO.hasSpaceGroupSymbol, None))):
    sg = str(o)
    altname = None
    if sg == "Im-3m": altname = "bcc"
    elif sg == "Fm-3m": altname = "fcc"
    elif sg == "Fd-3m": altname = "diamond"
    if altname:
        kg.graph.add((s, CMSO.hasAltName, Literal(altname)))
```

然后原 CQ2 才能跑。

### 3.4 CQ3:**第二个 drift!** Volume 是节点而不是字面量

按 README 写法跑会空。问题在于 atomRDF 实际生成:

```
?simcell  cmso:hasVolume         ?VolumeNode .
?VolumeNode  asmo:hasValue       23.64 .
?VolumeNode  asmo:hasUnit        unit:ANGSTROM3 .
```

但 README 写的 SPARQL 假设 `cmso:hasVolume` 直接给字面量。

**修复:**

```python
q3_fixed = """
PREFIX cmso: <http://purls.helmholtz-metadaten.de/cmso/>
PREFIX asmo: <http://purls.helmholtz-metadaten.de/asmo/>
SELECT DISTINCT ?sample ?vol
WHERE {     
    ?sample cmso:hasSimulationCell ?simcell .
    ?simcell cmso:hasVolume ?volNode .
    ?volNode asmo:hasValue ?vol .
    FILTER (?vol >= 10.0 && ?vol <= 80.0)
}"""
```

这正确返回所有体积在范围内的样本。

### 3.5 CQ4:跑通(没问题)

### 3.6 把 drift 记到复现报告里

| CQ | 问题 | 修复 |
|---|---|---|
| CQ1 | 无 | — |
| CQ2 | `hasAltName` 不被 atomRDF 自动生成 | 改用空间群+原子数;或手工补齐 |
| CQ3 | `hasVolume` 是节点,需要 `asmo:hasValue` 取值 | 加两跳 |
| CQ4 | 无 | — |

**这些发现写到你复现报告里就有 1–2 节内容,体现"批评性复现"。**

### 3.7 试用 atomRDF 的高级查询 API

atomRDF 还有一个隐藏功能,**用本体术语直接查,不写 SPARQL**:

```python
df = kg.query(
    kg.ontology.terms.cmso.AtomicScaleSample,
    [kg.ontology.terms.cmso.hasSpaceGroupSymbol,
     kg.ontology.terms.cmso.hasNumberOfAtoms]
)
print(df)
```

这背后是 `tools4RDF`——它在 ontology graph 里自动寻路,生成 SPARQL。这种"declarative query"是 atomRDF 比 MDO 工程范式更先进的地方。

### 阶段 3 验收

提交一个 `cq_results.py`,里面包含:
- 4 个原版 CQ 的运行结果(2 个失败,2 个成功)
- 修复后的 4 个 CQ 全部成功
- 一段叙述:"我发现的 documentation drift 是…"

---

## 阶段 4 — 缺陷:PODO 点缺陷 + PLDO 位错 (2 小时)

这是 CMSO 套件**真正不可替代**的功能——其他材料本体很少同时覆盖点缺陷、平面缺陷、线缺陷。

### 4.1 生成空位 (PODO)

```python
from atomrdf import KnowledgeGraph
from atomrdf.build import defect

kg = KnowledgeGraph()
atoms = defect.vacancy(
    "Fe", crystalstructure="bcc", a=2.87, cubic=True, repeat=3,
    no_of_vacancies=1, graph=kg
)
print(f"Built Fe BCC 3x3x3 supercell with 1 vacancy: {len(atoms)} atoms")
print(f"Triples: {len(kg.graph)}")
```

**预期输出:**
```
Built Fe BCC 3x3x3 supercell with 1 vacancy: 53 atoms (54-1)
Triples: 79
```

新增的 4 个缺陷三元组:
```
sample:xxx              --hasNumberOfVacancies         --> 1
sample:xxx_Material     --hasCrystallographicDefect    --> sample:xxx_Vacancy
sample:xxx_Vacancy      --rdf:type                     --> podo:Vacancy
sample:xxx              --hasVacancyConcentration      --> 0.0189 (= 1/53)
```

### 4.2 SPARQL 查询所有有缺陷的样本

```python
q = """
PREFIX cmso: <http://purls.helmholtz-metadaten.de/cmso/>
PREFIX podo: <http://purls.helmholtz-metadaten.de/podo/>

SELECT ?sample ?concentration
WHERE {
    ?sample podo:hasVacancyConcentration ?concentration .
}
ORDER BY ?concentration"""

df = kg.query(q)
print(df)
```

### 4.3 置换缺陷

```python
from atomrdf.build import defect

# Fe BCC 里替换一个原子为 Cr
atoms = defect.substitutional(
    "Fe", crystalstructure="bcc", a=2.87, cubic=True, repeat=3,
    substitution_element="Cr", no_of_substitutions=2, graph=kg
)
```

### 4.4 间隙缺陷(类似)

```python
atoms = defect.interstitial(
    "Fe", crystalstructure="bcc", a=2.87, cubic=True, repeat=3,
    interstitial_element="C", no_of_interstitials=1, graph=kg
)
```

### 4.5 位错 + 晶界(PLDO)

```python
from atomrdf.build.defect import dislocation, grain_boundary

# 这两个 API 用法比 vacancy 复杂,涉及晶向、Burgers vector 等参数
# 详细参考 atomRDF docs: https://atomrdf.pyscal.org/
help(dislocation)
help(grain_boundary)
```

### 4.6 跨缺陷类型查询

这是 CMSO 套件最优雅的地方——**同一套 SPARQL 模式,能查所有缺陷类型**:

```python
q = """
PREFIX cmso: <http://purls.helmholtz-metadaten.de/cmso/>
PREFIX podo: <http://purls.helmholtz-metadaten.de/podo/>
PREFIX pldo: <http://purls.helmholtz-metadaten.de/pldo/>

SELECT ?sample ?defectType
WHERE {
    ?sample cmso:hasMaterial ?material .
    ?material cmso:hasCrystallographicDefect ?defect .
    ?defect a ?defectType .
}"""

df = kg.query(q)
print(df)
```

### 阶段 4 验收

生成至少 3 种不同缺陷类型(空位、置换、间隙),用一个 SPARQL 同时查出所有缺陷类型和它们的浓度。

---

## 阶段 5 — ASMO:加入计算方法与属性 (1.5 小时)

CMSO 告诉你"算的是什么",ASMO 告诉你"用什么方法算 + 算出了什么"。

### 5.1 给样本加一个计算属性

atomRDF 用 `add_calculated_property` 这类 API 把 ASMO 整合进来。具体调用方式参考:

```python
from atomrdf import KnowledgeGraph
from atomrdf.build import bulk
from rdflib import Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF

kg = KnowledgeGraph()
atoms = bulk("Fe", crystalstructure="bcc", a=2.87, cubic=True, graph=kg)
sample_uri = URIRef(kg.sample_ids[0])

# 手工加 ASMO 三元组:一个能量计算
ASMO = Namespace("http://purls.helmholtz-metadaten.de/asmo/")
QUDT_UNIT = Namespace("http://qudt.org/vocab/unit/")

prop_node = URIRef(f"{sample_uri}_FormationEnergy")
val_node = BNode()

kg.graph.add((sample_uri, ASMO.hasCalculatedProperty, prop_node))
kg.graph.add((prop_node, RDF.type, ASMO.FormationEnergy))
kg.graph.add((prop_node, ASMO.hasValue, Literal(-0.05)))
kg.graph.add((prop_node, ASMO.hasUnit, QUDT_UNIT["EV"]))

print(f"After adding formation energy: {len(kg.graph)} triples")
```

### 5.2 计算方法:DFT + parameters

```python
# 把"这是用 DFT 算的"也写进去
METHOD = URIRef(f"{sample_uri}_Method")
ENCUT = BNode()

kg.graph.add((sample_uri, ASMO.hasComputationalMethod, METHOD))
kg.graph.add((METHOD, RDF.type, ASMO.DensityFunctionalTheory))
kg.graph.add((METHOD, ASMO.hasInputParameter, ENCUT))
kg.graph.add((ENCUT, RDF.type, ASMO.EnergyCutoff))
kg.graph.add((ENCUT, ASMO.hasValue, Literal(520)))
kg.graph.add((ENCUT, ASMO.hasUnit, QUDT_UNIT["EV"]))
```

### 5.3 跨本体查询:formation energy of BCC Fe

```python
q = """
PREFIX cmso: <http://purls.helmholtz-metadaten.de/cmso/>
PREFIX asmo: <http://purls.helmholtz-metadaten.de/asmo/>

SELECT ?sample ?formation_energy ?spacegroup
WHERE {
    ?sample cmso:hasMaterial ?m .
    ?m cmso:hasStructure ?s .
    ?s cmso:hasSpaceGroupSymbol ?spacegroup .
    
    ?sample asmo:hasCalculatedProperty ?prop .
    ?prop a asmo:FormationEnergy ;
          asmo:hasValue ?formation_energy .
}"""

df = kg.query(q)
print(df)
```

### 5.4 ASMO 还能描述什么

| ASMO 类 | 用途 |
|---|---|
| `DensityFunctionalTheory` | DFT 方法 |
| `AbInitioMolecularDynamics` | AIMD |
| `EmbeddedAtomModel` | EAM 势 |
| `InteratomicPotential` | 经典 MD 势 |
| `KineticMonteCarloMethod` | kMC |
| `KPointMesh`, `EnergyCutoff`, `Barostat` | 输入参数 |
| `FormationEnergy`, `FreeEnergy`, `BulkModulus`, `ElasticConstant` | 输出属性 |

### 阶段 5 验收

构建至少 3 个样本(BCC Fe / FCC Cu / FCC Al),每个都加上 formation energy 和 cutoff energy,然后用一个跨本体 SPARQL 查出来。

---

## 阶段 6 — Materials Project 集成 + Workflow Parser (1.5 小时)

### 6.1 Materials Project 集成(需要 API key)

```python
from atomrdf import KnowledgeGraph
from atomrdf.mp import query_mp

# 申请 API key: https://next-gen.materialsproject.org/api
api_key = "YOUR_API_KEY_HERE"

kg = KnowledgeGraph()
# 查所有稳定的 Fe-O 化合物
results = query_mp(api_key, chemical_system="Fe-O", is_stable=True)
print(f"Got {len(results)} MP entries")
```

`query_mp` 把 MP 的数据自动转成 CMSO/ASMO RDF。如果你没有 API key 也可以跳过这一步,**Materials Project 集成不是阶段必备**。

### 6.2 Workflow Parser:LAMMPS / VASP 输出转 RDF

这是 atomRDF 最强大的功能——直接解析计算输出文件。

```python
from atomrdf.io import WorkflowParser

# 假设你有一个 LAMMPS 输出目录
parser = WorkflowParser(kg=KnowledgeGraph(), debug=True)
parser.from_file("/path/to/lammps/output")
```

具体支持的格式参考 `atomrdf.io.workflow_parser` 源码。它的核心理念:**计算软件的输出文件本身就有结构,WorkflowParser 把这种结构映射到 CMSO+ASMO 的 RDF 形式**。

### 6.3 与 pyiron 的集成

atomRDF 原生支持 pyiron(原子模拟工作流框架):

```python
import pyiron_atomistics  # 可选
from atomrdf.parsers.pyiron import parse_job

# 一个 pyiron job 自动转 RDF
# job = pr.create.job.Lammps(...)
# kg = parse_job(job)
```

### 阶段 6 验收(可选)

- 如果有 MP API key:用 `query_mp` 拉至少 10 个稳定化合物,生成 KG
- 如果有 LAMMPS 经验:用 WorkflowParser 解析一个已有输出
- 如果都没有:只读 `atomrdf.parsers.pyiron` 源码,理解它解析的关键字段是哪些

---

## 阶段 7 — 可视化 + 持久化 + 复现报告 (1 小时)

### 7.1 可视化 RDF 知识图谱

```python
from atomrdf import KnowledgeGraph
from atomrdf.build import bulk

kg = KnowledgeGraph()
bulk("Fe", crystalstructure="bcc", a=2.87, cubic=True, graph=kg)

# 用 graphviz 渲染整个 KG
g = kg.visualise(rankdir="BT", layout="dot")
g.render("/tmp/kg_visualization", format="svg")
```

会生成一个 SVG 文件,显示样本/材料/晶体结构/原子等节点之间的所有关系。这是给导师汇报时最直观的素材。

### 7.2 多个样本只看 sample-level 视图

```python
g = kg.visualise(sample_view=True)
g.render("/tmp/sample_view", format="svg")
```

### 7.3 持久化整个 KG

```python
# 导出 turtle
with open('full_kg.ttl', 'w') as f:
    f.write(kg.graph.serialize(format='turtle'))

# 用 archive 方法保存(包含结构信息文件)
kg.archive('my_workspace')
# 之后可以用 KnowledgeGraph.unarchive('my_workspace') 还原
```

### 7.4 复现报告模板

```markdown
# CMSO + atomRDF 复现报告

## 1. 工具版本
- atomRDF: x.y.z (`pip show atomrdf`)
- CMSO commit: <git rev-parse --short HEAD>
- 复现日期: 2026-XX-XX
- Python: 3.X.X

## 2. 我复现的范围
- ✅ 阶段 0-5 全部
- ✅ 阶段 6 部分(WorkflowParser,无 MP API key)
- ✅ 阶段 7 可视化生成 3 个 SVG

## 3. 4 个 CQ 的结果
- CQ1: ✓ 直接成功
- CQ2: ✗ documentation drift,需修复(`hasAltName` 不存在)
- CQ3: ✗ documentation drift,需修复(Volume 是节点而非字面量)
- CQ4: ✓ 直接成功

## 4. 关键发现
### Documentation drift 列表
...

### atomRDF API 与 docstring 的不一致
- `bulk()` 实际只返回 ase.Atoms,但 docstring 说返回 tuple
- `to_file()` 名字误导,它不写 RDF,是写 LAMMPS data 文件
- ...

## 5. CMSO 设计的优缺点(对你 mag-material-ontology 的启示)
### 优点
- 模块化清晰(CMSO 样本 + ASMO 方法 + PODO/PLDO/LDO 缺陷)
- "Upper-ontology-agnostic"——没绑 BFO 或 EMMO,容易借鉴
- 外部锚定:元素用 ChEBI,晶系用 Wikidata
- atomRDF 实现了"本体即代码":Python API 自动生成 RDF

### 缺点
- 4 个 CQ 太少,生产级使用要参考 Guzmán 2026 arXiv 论文(750K triples 案例)
- Documentation drift 较多
- 没有 SHACL 约束
- 没覆盖磁性属性

## 6. 给我自己工作的启示——mag-cmso 草稿
我可以构建:
- `mag-cmso`:复用 CMSO AtomicScaleSample,新增 MagneticSample 加上 magnetic moment per atom
- `mag-asmo`:扩展 ASMO,加 MicromagneticSimulation, SpinDynamicsSimulation, MonteCarloSimulation
- `mag-pldo`:磁畴壁(domain wall)是磁性领域的特有"平面缺陷"
- `atomrdf-mag`:fork atomRDF 加 magnetic moment 生成函数
```

### 阶段 7 验收

至少 3 张 SVG 图(单样本视图 + 多样本视图 + 缺陷视图)+ 完整的复现报告 md 文件。

---

## 常见错误与排查

| 错误 | 原因 | 解决 |
|---|---|---|
| `pip install atomrdf` 报 PEP 668 | Ubuntu 24+ 系统 Python 保护 | 用 venv,不要直接 pip 进系统 |
| `ImportError: cannot import name 'System'` | 旧文档误导 | 用 `from atomrdf.build import bulk` |
| `bulk()` 返回不是 tuple | docstring drift | 用 `kg.sample_ids[0]` 获取 sample URI |
| CQ2 SPARQL 返回空 | `hasAltName` 不被生成 | 改用空间群+原子数;或手工补齐 |
| CQ3 SPARQL 返回空 | Volume 是节点不是字面量 | 加 `asmo:hasValue` 一跳 |
| `visualise` 报 graphviz not found | 系统没装 graphviz | `apt install graphviz` 或 `brew install graphviz` |
| `to_file` 不生成 RDF | API 命名误导 | 用 `kg.graph.serialize()` |
| `query_mp` 报 401 | 没 MP API key | 跳过这步或申请 https://next-gen.materialsproject.org/api |

---

## 关键资源

- **CMSO 仓库:** https://github.com/OCDO/cmso-ontology
- **CMSO 文档:** https://ocdo.github.io/cmso/
- **OCDO 套件:** https://github.com/OCDO
- **atomRDF 仓库:** https://github.com/pyscal/atomRDF
- **atomRDF 文档:** https://atomrdf.pyscal.org/
- **大规模案例论文:** Guzmán et al. 2026 arXiv:2604.06230 (750K triples)
- **作者:** Abril Azocar Guzman (a.azocar.guzman@fz-juelich.de, FZJ IAS-9)
- **基金:** NFDI-MatWerk (DFG NFDI 38/1, 项目 460247524)

---

## 进度自查清单

- [ ] 阶段 0:`pip show atomrdf` 显示已安装,5 个本体 clone 完成
- [ ] 阶段 1:能口述 CMSO/ASMO/PLDO/PODO/LDO 各自职责
- [ ] 阶段 2:跑通 bulk("Fe") 生成 75 triples
- [ ] 阶段 3:4 个 CQ 全部跑出结果(必要时修复),记录 drift
- [ ] 阶段 4:生成 3 种缺陷,SPARQL 同时查出所有类型
- [ ] 阶段 5:手动加 ASMO formation energy 与 DFT 方法
- [ ] 阶段 6:或读 MP 数据,或读 LAMMPS,或跳过
- [ ] 阶段 7:3 张 SVG + 完整复现报告

## 与 MDO 复现的对比反思

跑完 CMSO 复现后,你应该已经体会到:

| 维度 | MDO | CMSO+atomRDF |
|---|---|---|
| 学到的 OWL 设计 | 模块化、import 单向、CQ-SPARQL 对应 | 多本体协同、外部锚定、规模分级 |
| 学到的工程 | SPARQL-Generate JSON 映射 | Python API 自动生成 RDF |
| 学到的"陷阱" | SPARQL 与数据预期不一致 | Docstring 与实际行为不一致 |
| 复现产出 | 一个 KG + 14 CQ 修复版 | 多个样本/缺陷 KG + 跨本体 SPARQL |
| 哪个更适合磁性领域 | 偏数据库集成场景 | **偏计算样本管理场景,更接近你的需求** |

**复现完两个**,你就完整掌握了"computational materials ontology"的两条主流工程范式——这是你给导师汇报"为什么我选 X 路线"时的最强论据。
