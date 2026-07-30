"""
工艺知识Agent工具集（RAG增强版）
基于焊接知识库回答工艺参数推荐、缺陷诊断等问题。
优先使用RAG真实检索，失败时回退到内置知识库。
"""
from langchain_core.tools import tool

from src.agents.rag.retriever import hybrid_search, retrieve_knowledge


# 焊接工艺知识库（内置，作为RAG的补充/兜底）
WELDING_KNOWLEDGE = {
    "Q235": {
        "thickness_10mm": {
            "process": "CO2气体保护焊 (GMAW)",
            "current": "220-280A",
            "voltage": "28-32V",
            "speed": "300-500 mm/min",
            "wire": "ER70S-6, 1.2mm",
            "gas": "CO2或80%Ar+20%CO2, 15-20 L/min",
            "preheat": "一般不需要预热（环境温度>5℃时）",
            "notes": "Q235碳当量低，焊接性好。10mm板建议开V型坡口，钝边2mm，间隙2-3mm。多层焊时层间温度控制在150-200℃。",
        },
        "thickness_6mm": {
            "process": "CO2气体保护焊 (GMAW)",
            "current": "180-240A",
            "voltage": "24-28V",
            "speed": "400-600 mm/min",
            "wire": "ER70S-6, 1.2mm",
            "gas": "CO2, 15-20 L/min",
            "preheat": "不需要预热",
            "notes": "6mm板可不开坡口，留1-2mm间隙，单面焊双面成型。",
        },
    },
    "Q345": {
        "thickness_10mm": {
            "process": "CO2气体保护焊 (GMAW) 或 埋弧自动焊",
            "current": "240-300A",
            "voltage": "30-34V",
            "speed": "300-450 mm/min",
            "wire": "ER50-6, 1.2mm",
            "gas": "80%Ar+20%CO2, 18-22 L/min",
            "preheat": "环境温度<0℃时预热100-150℃",
            "notes": "Q345碳当量略高于Q235，低合金高强钢。注意控制热输入，避免热影响区脆化。",
        },
    },
    "SUS304": {
        "thickness_3mm": {
            "process": "TIG焊 (GTAW)",
            "current": "90-130A",
            "voltage": "12-16V",
            "speed": "150-250 mm/min",
            "wire": "ER308, 1.6mm",
            "gas": "纯Ar, 8-12 L/min",
            "preheat": "不需要预热",
            "notes": "不锈钢导热系数低，热膨胀系数大，注意控制变形。焊接时电流比碳钢小10-20%。",
        },
    },
}

# 焊接缺陷诊断知识库
DEFECT_DIAGNOSIS = {
    "气孔": {
        "causes": ["保护气体流量不足或过大", "焊丝受潮", "工件表面有油污/铁锈", "风速过大吹散保护气"],
        "solutions": ["调整气体流量至15-25L/min", "使用前烘干焊丝", "焊前清理工件表面", "设置防风屏障"],
    },
    "夹渣": {
        "causes": "前层焊道清理不干净、焊接电流过小、焊接速度过慢",
        "solutions": "层间打磨清理、适当增大电流、提高焊接速度",
    },
    "未焊透": {
        "causes": "坡口角度过小、钝边过大、电流过小、焊接速度过快",
        "solutions": "增大坡口角度至55-65°、减小钝边至1-2mm、增大电流10-20A、降低焊速",
    },
    "裂纹": {
        "causes": "拘束应力过大、焊缝含氢量高、冷却速度过快、母材碳当量高",
        "solutions": "预热降低冷却速度、使用低氢焊丝、合理安排焊接顺序减小应力、焊后热处理",
    },
    "咬边": {
        "causes": "电流过大、电弧过长、焊接速度过快、焊枪角度不当",
        "solutions": "减小电流、压低电弧长度、降低焊速、调整焊枪角度至70-80°",
    },
}


@tool
def recommend_welding_parameters(material: str, thickness: str) -> dict:
    """推荐焊接工艺参数。根据母材材质和板厚推荐焊接方法、电流、电压、焊丝等。
    优先从RAG知识库检索真实文档，失败时回退到内置知识库。

    Args:
        material: 母材材质，例如 Q235、Q345、SUS304
        thickness: 板厚描述，例如 10mm、6mm、3mm
    """
    # 策略1：优先尝试RAG检索
    try:
        query = f"{material} {thickness}板 焊接工艺参数推荐 电流 电压 焊速"
        rag_docs = hybrid_search(query, top_k=2, use_query_expansion=True)
        if rag_docs and len(rag_docs) > 0:
            return {
                "material": material,
                "thickness": thickness,
                "recommendation": {
                    "process": "基于知识库RAG检索结果",
                    "rag_context": [doc.page_content for doc in rag_docs],
                    "sources": [doc.metadata.get("source", "unknown") for doc in rag_docs],
                },
                "source": "RAG知识库检索",
            }
    except Exception as e:
        print(f"[KnowledgeTool] RAG检索失败，回退到内置知识库: {e}")

    # 策略2：回退到内置硬编码知识库
    key = f"thickness_{thickness}"
    data = WELDING_KNOWLEDGE.get(material, {}).get(key)
    if data:
        return {
            "material": material,
            "thickness": thickness,
            "recommendation": data,
            "source": "焊接工艺知识库(内置)",
        }
    # 兜底推荐
    return {
        "material": material,
        "thickness": thickness,
        "recommendation": {
            "process": "建议参考焊接工艺手册，根据具体材质和厚度选择合适工艺",
            "general_rule": "碳钢一般采用CO2气体保护焊，不锈钢采用TIG焊，厚度>12mm建议开坡口多层焊",
        },
        "source": "通用建议",
    }


@tool
def diagnose_welding_defect(defect_type: str) -> dict:
    """诊断焊接缺陷，给出原因分析和解决方案。
    优先从RAG知识库检索真实案例，失败时回退到内置诊断库。

    Args:
        defect_type: 缺陷类型，例如 气孔、夹渣、未焊透、裂纹、咬边
    """
    # 策略1：优先尝试RAG检索
    try:
        query = f"焊接缺陷 {defect_type} 原因分析 解决方案 预防措施"
        rag_docs = hybrid_search(query, top_k=2, use_query_expansion=True)
        if rag_docs and len(rag_docs) > 0:
            return {
                "defect": defect_type,
                "causes": [doc.page_content[:200] for doc in rag_docs],  # RAG返回的上下文作为原因参考
                "solutions": ["请参考上述知识库内容中的解决方案"],
                "rag_sources": [doc.metadata.get("source", "unknown") for doc in rag_docs],
                "source": "RAG知识库检索",
            }
    except Exception as e:
        print(f"[KnowledgeTool] RAG检索失败，回退到内置诊断库: {e}")

    # 策略2：回退到内置硬编码诊断库
    data = DEFECT_DIAGNOSIS.get(defect_type)
    if data:
        return {
            "defect": defect_type,
            "causes": data["causes"],
            "solutions": data["solutions"],
            "source": "焊接缺陷诊断知识库(内置)",
        }
    return {
        "defect": defect_type,
        "error": f"暂无'{defect_type}'的诊断数据，支持: {list(DEFECT_DIAGNOSIS.keys())}",
    }


@tool
def search_welding_standards(keyword: str) -> dict:
    """搜索焊接相关标准与规范。
    优先从RAG知识库检索标准文档，失败时回退到内置标准列表。

    Args:
        keyword: 搜索关键词，例如 GB/T、ISO、ASME
    """
    # 策略1：优先尝试RAG检索
    try:
        query = f"焊接标准 规范 {keyword}"
        rag_docs = hybrid_search(query, top_k=3)
        if rag_docs and len(rag_docs) > 0:
            return {
                "keyword": keyword,
                "matched_count": len(rag_docs),
                "standards": [
                    {"code": doc.metadata.get("source", ""), "name": doc.page_content[:200]}
                    for doc in rag_docs
                ],
                "source": "RAG知识库检索",
            }
    except Exception as e:
        print(f"[KnowledgeTool] RAG检索失败，回退到内置标准列表: {e}")

    # 策略2：回退到内置硬编码标准列表
    standards = [
        {"code": "GB/T 985.1-2008", "name": "气焊、焊条电弧焊、气体保护焊和高能束焊的推荐坡口"},
        {"code": "GB/T 19867.1-2005", "name": "电弧焊焊接工艺规程"},
        {"code": "GB/T 3323-2005", "name": "金属熔化焊焊接接头射线照相"},
        {"code": "ISO 9606-1:2017", "name": "焊工考试 熔化焊 第1部分:钢"},
        {"code": "ASME BPVC Section IX", "name": "焊接、钎焊和粘接评定"},
    ]
    matched = [s for s in standards if keyword.upper() in s["code"].upper() or keyword in s["name"]]
    return {
        "keyword": keyword,
        "matched_count": len(matched),
        "standards": matched if matched else standards,
        "source": "内置标准列表",
    }


@tool
def rag_search(query: str, top_k: int = 3) -> dict:
    """通用RAG知识库检索工具。对任意焊接相关问题进行语义检索，返回最相关的知识库内容。

    当用户的问题无法被参数推荐/缺陷诊断等专用工具覆盖时，使用此工具进行开放式检索。

    Args:
        query: 用户的问题或查询文本
        top_k: 返回结果数量，默认3条
    """
    try:
        # 使用混合检索（向量+BM25+RRF融合）
        docs = hybrid_search(query, top_k=top_k, use_query_expansion=True)
        if not docs:
            return {
                "query": query,
                "results": [],
                "message": "未在知识库中找到相关内容",
            }

        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "category": doc.metadata.get("category", ""),
                "rrf_score": doc.metadata.get("_rrf_score"),
            })

        return {
            "query": query,
            "result_count": len(results),
            "results": results,
            "message": f"从知识库中检索到 {len(results)} 条相关内容",
        }
    except Exception as e:
        return {
            "query": query,
            "error": f"RAG检索失败: {str(e)}",
            "results": [],
        }


# 导出所有工具（供Agent系统注册使用）
KNOWLEDGE_TOOLS = [
    recommend_welding_parameters,
    diagnose_welding_defect,
    search_welding_standards,
    rag_search,  # 新增：通用RAG检索工具
]
