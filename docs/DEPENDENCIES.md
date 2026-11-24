# Dependency choices and API references

The implementation was checked against current official documentation and the installed runtime. Exact installed versions are recorded in `requirements-lock.txt` and `evaluation/results/environment.json`; `pip check` is included in the validation log. Pinning records the tested environment, not a promise that every OS/Python combination works.

| Dependency | Role | Official reference |
|---|---|---|
| FastAPI + Pydantic | Typed HTTP endpoints, multipart uploads and validation | [FastAPI upload documentation](https://fastapi.tiangolo.com/tutorial/request-files/) |
| OpenAI Python SDK | OpenAI Responses or Google's Gemini-compatible Chat Completions for structured extraction/answers and function calls | [Gemini compatibility](https://ai.google.dev/gemini-api/docs/openai), [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [function calling](https://developers.openai.com/api/docs/guides/function-calling) |
| FastEmbed | Local ONNX BGE embeddings | [Local FastEmbed documentation](https://qdrant.tech/documentation/embeddings/fastembed/) |
| Qdrant client | Embedded disk-backed vector database | [Python client local mode](https://github.com/qdrant/qdrant-client) |
| scikit-learn | Explicit TF-IDF lexical baseline | [TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html) |
| pypdf | Actual-page text extraction | [Text extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) |
| Streamlit | Native forms, tables, session state and headless UI tests | [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest) |
| ReportLab | Reproducible synthetic PDFs, two readable layouts | [ReportLab documentation](https://docs.reportlab.com/) |
| pypdfium2 | Local PDF render inspection fallback when Poppler is unavailable | [pypdfium2](https://pypdfium2.readthedocs.io/) |

The host Streamlit skill and installed Streamlit reference documentation were read before implementation. No orchestration framework is needed: the assistant uses a bounded loop with three tools.
