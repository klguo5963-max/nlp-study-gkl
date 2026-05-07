"""
意图分类服务主程序（带 CORS）
v0.10 — endpoint 异常处理提取 + traceback 截断

启动: uvicorn main_cors:app --reload --host 0.0.0.0 --port 8000
"""
import time
import traceback

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from data_schema import TextClassifyRequest, TextClassifyResponse
from logger import logger
from model.regex_rule import model_for_regex
from model.tfidf_ml import model_for_tfidf
from model.bert import model_for_bert
from model.prompt import model_for_llm

app = FastAPI(
    title="意图分类服务",
    description="支持正则、TF-IDF、BERT、LLM 四种模型",
    version="0.10.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _handle_exception(resp, req):
    """
    统一处理异常：完整堆栈写入日志，前端只收到友好提示
    """
    resp.classify_result = "" if isinstance(req.request_text, str) else []
    resp.error_msg = "模型分类异常，请查看服务端日志"
    logger.error(f"[{req.request_id}] 分类异常:\n{traceback.format_exc()}")


@app.get("/")
def health_check():
    """健康检查"""
    logger.info("健康检查被调用")
    return {
        "service": "意图分类服务",
        "version": "0.10.0",
        "status": "running",
        "endpoints": {
            "regex": "/v1/text-cls/regex",
            "tfidf": "/v1/text-cls/tfidf",
            "bert": "/v1/text-cls/bert",
            "gpt": "/v1/text-cls/gpt",
        },
        "docs": "/docs",
    }


@app.post("/v1/text-cls/regex", response_model=TextClassifyResponse)
def regex_classify(req: TextClassifyRequest) -> TextClassifyResponse:
    """正则匹配分类"""
    start = time.time()
    resp = TextClassifyResponse(
        request_id=req.request_id,
        request_text=req.request_text,
    )
    logger.info(f"[regex] {req.request_id} | {req.request_text}")

    try:
        result = model_for_regex(req.request_text)
        resp.classify_result = result
        resp.error_msg = "ok"
    except Exception:
        _handle_exception(resp, req)

    resp.classify_time = round(time.time() - start, 3)
    return resp


@app.post("/v1/text-cls/tfidf", response_model=TextClassifyResponse)
def tfidf_classify(req: TextClassifyRequest) -> TextClassifyResponse:
    """TF-IDF 分类"""
    start = time.time()
    resp = TextClassifyResponse(
        request_id=req.request_id,
        request_text=req.request_text,
    )
    logger.info(f"[tfidf] {req.request_id} | {req.request_text}")

    try:
        result = model_for_tfidf(req.request_text)
        resp.classify_result = result
        resp.error_msg = "ok"
    except Exception:
        _handle_exception(resp, req)

    resp.classify_time = round(time.time() - start, 3)
    return resp


@app.post("/v1/text-cls/bert", response_model=TextClassifyResponse)
def bert_classify(req: TextClassifyRequest) -> TextClassifyResponse:
    """BERT 分类"""
    start = time.time()
    resp = TextClassifyResponse(
        request_id=req.request_id,
        request_text=req.request_text,
    )
    logger.info(f"[bert] {req.request_id} | {req.request_text}")

    try:
        result = model_for_bert(req.request_text)
        resp.classify_result = result
        resp.error_msg = "ok"
    except Exception:
        _handle_exception(resp, req)

    resp.classify_time = round(time.time() - start, 3)
    return resp


@app.post("/v1/text-cls/gpt", response_model=TextClassifyResponse)
def llm_classify(req: TextClassifyRequest) -> TextClassifyResponse:
    """LLM 分类"""
    start = time.time()
    resp = TextClassifyResponse(
        request_id=req.request_id,
        request_text=req.request_text,
    )
    logger.info(f"[gpt] {req.request_id} | {req.request_text}")

    try:
        result = model_for_llm(req.request_text)
        resp.classify_result = result
        resp.error_msg = "ok"
    except Exception:
        _handle_exception(resp, req)

    resp.classify_time = round(time.time() - start, 3)
    return resp


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
