from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import PreviewRequest, PreviewResponse, ErrorResponse
from .services.fetch import preview_from_url
from .core.settings import settings
import httpx
import logging
# from opentelemetry import trace
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.resources import Resource
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
# from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IGniter", version="2.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# if settings.ENABLE_OTEL:
#     logger.info("OpenTelemetry enabled. Setting up tracing.")
#     try:
#         resource = Resource(attributes={"service.name": "url-previewer-api"})
#         provider = TracerProvider(resource=resource)
#         exporter = OTLPSpanExporter()
#         span_processor = BatchSpanProcessor(exporter)
#         provider.add_span_processor(span_processor)
#         trace.set_tracer_provider(provider)
#         FastAPIInstrumentor.instrument_app(app)
#         logger.info("OpenTelemetry tracing enabled successfully.")
#     except Exception as e:
#         logger.error(f"Failed to initialize OpenTelemetry tracing: {e}", exc_info=True)
#         logger.warning("OpenTelemetry tracing disabled due to initialization error.")

@app.post("/api/preview", response_model=PreviewResponse, responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}, 504: {"model": ErrorResponse}})
async def preview(payload: PreviewRequest):
    url = str(payload.url)
    try:
        data = await preview_from_url(url)
        return PreviewResponse(**data)
    except httpx.TimeoutException:
        logger.error(f"Timeout while fetching '{url}'")
        raise HTTPException(status_code=504, detail=f"Request to '{url}' timed out. The server took too long to respond.")
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        logger.error(f"HTTP error {status_code} while fetching '{url}': {e}")
        raise HTTPException(status_code=400, detail=f"Could not retrieve content from '{url}'. The remote server responded with status {status_code}.")
    except httpx.ConnectError as e:
        logger.error(f"Connection error while fetching '{url}': {e}")
        raise HTTPException(status_code=503, detail=f"Could not connect to '{url}'. Please check your internet connection or the URL.")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error while fetching '{url}': {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch '{url}': {str(e)}")
    except Exception as e:
        logger.critical(f"Unexpected error while processing '{url}': {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Failed to fetch or parse the URL")