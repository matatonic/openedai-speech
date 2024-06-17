from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from loguru import logger

class OpenAIError(Exception):
    pass

class APIError(OpenAIError):
    message: str
    code: str = None
    param: str = None
    type: str = None

    def __init__(self, message: str, code: int = 500, param: str = None, internal_message: str = ''):
        super().__init__(message)
        self.message = message
        self.code = code
        self.param = param
        self.type = self.__class__.__name__,
        self.internal_message = internal_message

    def __repr__(self):
        return "%s(message=%r, code=%d, param=%s)" % (
            self.__class__.__name__,
            self.message,
            self.code,
            self.param,
        )

class InternalServerError(APIError):
    pass

class ServiceUnavailableError(APIError):
    def __init__(self, message="Service unavailable, please try again later.", code=503, internal_message=''):
        super().__init__(message, code, internal_message)

class APIStatusError(APIError):
    status_code: int = 400
    
    def __init__(self, message: str, param: str = None, internal_message: str = ''):
        super().__init__(message, self.status_code, param, internal_message)

class BadRequestError(APIStatusError):
    status_code: int = 400

class AuthenticationError(APIStatusError):
    status_code: int = 401

class PermissionDeniedError(APIStatusError):
    status_code: int = 403

class NotFoundError(APIStatusError):
    status_code: int = 404

class ConflictError(APIStatusError):
    status_code: int = 409

class UnprocessableEntityError(APIStatusError):
    status_code: int = 422

class RateLimitError(APIStatusError):
    status_code: int = 429

class OpenAIStub(FastAPI):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.models = {}

        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

        @self.exception_handler(Exception)
        def openai_exception_handler(request: Request, exc: Exception) -> JSONResponse:
            # Generic server errors
            #logger.opt(exception=exc).error("Logging exception traceback")

            return JSONResponse(status_code=500, content={
                'message': 'InternalServerError',
                'code': 500,
            })

        @self.exception_handler(APIError)
        def openai_apierror_handler(request: Request, exc: APIError) -> JSONResponse:
            # Server error
            logger.opt(exception=exc).error("Logging exception traceback")

            if exc.internal_message:
                logger.info(exc.internal_message)

            return JSONResponse(status_code = exc.code, content={
                'message': exc.message,
                'code': exc.code,
                'type': exc.__class__.__name__,
                'param': exc.param,
            })

        @self.exception_handler(APIStatusError)
        def openai_statuserror_handler(request: Request, exc: APIStatusError) -> JSONResponse:
            # Client side error
            logger.info(repr(exc))

            if exc.internal_message:
                logger.info(exc.internal_message)

            return JSONResponse(status_code = exc.code, content={
                'message': exc.message,
                'code': exc.code,
                'type': exc.__class__.__name__,
                'param': exc.param,
            })

        @self.middleware("http")
        async def log_requests(request: Request, call_next):
            logger.debug(f"Request path: {request.url.path}")
            logger.debug(f"Request method: {request.method}")
            logger.debug(f"Request headers: {request.headers}")
            logger.debug(f"Request query params: {request.query_params}")
            logger.debug(f"Request body: {await request.body()}")

            response = await call_next(request)

            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")

            return response

        @self.get('/v1/billing/usage')
        @self.get('/v1/dashboard/billing/usage')
        async def handle_billing_usage():
            return { 'total_usage': 0 }

        @self.get("/", response_class=PlainTextResponse)
        @self.head("/", response_class=PlainTextResponse)
        @self.options("/", response_class=PlainTextResponse)
        async def root():
            return PlainTextResponse(content="", status_code=200 if self.models else 503)

        @self.get("/health")
        async def health():
            return {"status": "ok" if self.models else "unk" }

        @self.get("/v1/models")
        async def get_model_list():
            return self.model_list()

        @self.get("/v1/models/{model}")
        async def get_model_info(model_id: str):
            return self.model_info(model_id)

    def register_model(self, name: str, model: str = None) -> None:
        self.models[name] = model if model else name

    def deregister_model(self, name: str) -> None:
        if name in self.models:
            del self.models[name]

    def model_info(self, model: str) -> dict:
        result = {
            "id": model,
            "object": "model",
            "created": 0,
            "owned_by": "user"
        }
        return result

    def model_list(self) -> dict:
        if not self.models:
            return {}
        
        result = {
            "object": "list",
            "data": [ self.model_info(model) for model in list(set(self.models.keys() | self.models.values())) if model ]
        }

        return result
