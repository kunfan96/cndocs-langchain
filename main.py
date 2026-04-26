import asyncio
import re
import logging
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── 项目专有名词（翻译时保持原文不翻译） ──────────────────────────────
TECHNICAL_TERMS = [
    # LangChain 生态
    "LangChain", "LangGraph", "LangSmith", "LangServe",
    # 编程语言 / 运行时
    "Python", "JavaScript", "TypeScript", "Node.js",
    # AI / LLM 相关
    "LLM", "GPT", "OpenAI", "Anthropic", "Claude", "Gemini",
    "Hugging Face", "HuggingFace", "Ollama", "vLLM", "GGUF",
    "ChatGPT", "DeepSeek", "Qwen", "Mistral", "LLaMA", "Llama",
    "Cohere", "Bedrock", "Azure", "AWS", "GCP",
    # 技术概念（保留英文）
    "Transformer", "Embedding", "Token", "Tokenizer",
    "RAG", "ReAct", "Chain of Thought", "CoT",
    "Fine-tuning", "Prompt", "Prompt Template",
    "Vector Store", "Retriever", "Document Loader",
    "Callback", "Runnable", "RunnableSequence",
    "LCEL", "API", "REST", "GraphQL", "SDK", "CLI",
    "MCP", "A2A", "ACP",
    # 数据库 / 存储
    "Redis", "PostgreSQL", "MongoDB", "Pinecone", "Chroma",
    "FAISS", "Weaviate", "Milvus", "Qdrant", "Neo4j",
    "Elasticsearch", "Cassandra", "SQLite", "MySQL",
    "Supabase", "Firebase", "DynamoDB", "BigQuery",
    # 框架 / 工具
    "FastAPI", "Flask", "Django", "Streamlit", "Gradio",
    "Docker", "Kubernetes", "Terraform", "GitHub", "GitLab",
    "Jupyter", "Notebook", "pandas", "NumPy", "PyTorch",
    "TensorFlow", "scikit-learn", "Pydantic",
    # 格式
    "Markdown", "MDX", "JSON", "YAML", "TOML", "CSV", "PDF",
    "HTML", "XML", "RSS", "SQL",
]

# ── 翻译系统提示词 ──────────────────────────────────────────────────
SYSTEM_PROMPT = """\
你是一位高质量的大型英文文档翻译专家，支持术语一致性、分段处理与格式保留。

## 翻译要求

1. **逐句翻译**：不得总结、删减或跳过任何内容。
2. **保留所有格式**：Markdown、列表、标题、表格、代码块、frontmatter (YAML between ---) 等全部保留原始结构。
3. **术语一致性**：在整篇文档中保持术语翻译一致。
4. **翻译风格**：技术文档风格（technical），准确、简洁、专业。
5. **输出要求**：
   - 输出结构必须与原文完全一致。
   - 不得添加解释、注释或额外内容。
   - 不得合并或拆分段落。
6. **Frontmatter 处理**：YAML frontmatter 中的 `title` 和 `description` 等值需要翻译，但键名保持不变。`sidebarTitle` 也需翻译。
7. **代码块**：代码块内的代码不翻译，但代码块内的注释可以翻译。
8. **链接**：保留原始链接地址不变，仅翻译链接文字（如果是描述性文字）。

## 输出格式

直接输出翻译后的完整文档内容，不要添加任何额外说明或包装。

"""

USER_PROMPT = """\
请将以下英文 MDX 文档翻译成中文，保留所有 Markdown/MDX 格式：

```mdx
{content}
```
"""

# ── 工作目录 ──────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
PROGRESS_FILE = BASE_DIR / "mdx-translation-progress.md"
MAX_CONCURRENCY = 100


def parse_file_list() -> list[str]:
    """从 mdx-translation-progress.md 解析需要翻译的文件路径（翻译进度为 0）。"""
    text = PROGRESS_FILE.read_text(encoding="utf-8")
    files: list[str] = []
    for line in text.splitlines():
        m = re.match(r"\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|", line)
        if m and int(m.group(2)) == 0:
            files.append(m.group(1))
    return files


def build_chain():
    """构建 LangChain 翻译链。"""
    llm = ChatOpenAI(
        base_url="https://api.xiaomimimo.com/v1",
        api_key="",
        model="mimo-v2-flash",
        temperature=0.1,
    )

    terms_str = "、".join(TECHNICAL_TERMS)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT),
    ])

    chain = prompt | llm | StrOutputParser()
    return chain, terms_str


async def translate_file(
    semaphore: asyncio.Semaphore, chain, terms_str: str, rel_path: str
) -> bool:
    """翻译单个文件并写回原路径。"""
    async with semaphore:
        src = BASE_DIR / rel_path
        if not src.exists():
            logger.warning("文件不存在，跳过: %s", rel_path)
            return False

        content = src.read_text(encoding="utf-8")
        if not content.strip():
            logger.warning("文件为空，跳过: %s", rel_path)
            return False

        logger.info("开始翻译: %s", rel_path)
        try:
            translated = await chain.ainvoke({
                "terms": terms_str,
                "content": content,
            })
            # 去除模型可能包裹的 ```mdx ... ``` 外壳
            translated = re.sub(r"^```mdx\s*\n", "", translated)
            translated = re.sub(r"\n```\s*$", "", translated)

            src.write_text(translated, encoding="utf-8")
            update_progress(rel_path, 100)
            logger.info("翻译完成: %s", rel_path)
            return True
        except Exception:
            logger.exception("翻译失败: %s", rel_path)
            update_progress(rel_path, 50)
            return False


def update_progress(rel_path: str, status: int):
    """更新 mdx-translation-progress.md 中对应文件的进度。

    status: 0=未开始, 50=错误, 100=完成
    """
    try:
        text = PROGRESS_FILE.read_text(encoding="utf-8")
        escaped = re.escape(rel_path)
        text = re.sub(
            rf"(\|\s*`{escaped}`\s*\|\s*)\d+(\s*\|)",
            rf"\g<1>{status}\2",
            text,
        )
        PROGRESS_FILE.write_text(text, encoding="utf-8")
    except Exception:
        logger.exception("更新进度失败: %s", rel_path)


async def main():
    files = parse_file_list()
    logger.info("待翻译文件共 %d 个", len(files))

    if not files:
        logger.info("没有需要翻译的文件")
        return

    chain, terms_str = build_chain()
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    tasks = [translate_file(semaphore, chain, terms_str, f) for f in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success = sum(1 for r in results if r is True)
    fail = len(files) - success

    logger.info(
        "全部翻译任务完成: 共 %d 成功, %d 失败",
        success,
        fail,
    )


if __name__ == "__main__":
    asyncio.run(main())
