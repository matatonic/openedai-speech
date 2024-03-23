from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

class OpenAIStub(FastAPI):
    def __init__(self) -> None:
        super().__init__()
        self.models = {}
            
        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )

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
