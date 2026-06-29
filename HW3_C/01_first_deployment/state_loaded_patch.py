"""
state_loaded_patch.py — Reference patch for HW3_B/app/main.py
Shows the diff to add /healthz/live and /healthz/ready endpoints,
and the state.loaded flag pattern.

You must apply this patch (or equivalent) to your HW3_B/app/main.py
before building the v1 image for HW3_C.

Add these imports to the top of app/main.py:
    from fastapi import Response, status

Add these endpoints after your existing routes:
    @app.get("/healthz/live")
    def healthz_live():
        return {"status": "live"}

    @app.get("/healthz/ready")
    def healthz_ready(response: Response):
        if getattr(app.state, "loaded", False):
            return {"status": "ready", "model_loaded": True}
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "model_loaded": False}

In your startup event (or wherever you load the model), AFTER the
model + tokenizer are loaded into memory, add:
    app.state.loaded = True

If you don't already have a startup event, here's the FastAPI way:
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Load model + tokenizer HERE
        app.state.model = AutoModel.from_pretrained(BUNDLE_DIR)
        app.state.tokenizer = AutoTokenizer.from_pretrained(BUNDLE_DIR)
        app.state.loaded = True
        yield
        # Cleanup on shutdown
        app.state.loaded = False

    app = FastAPI(lifespan=lifespan)
"""
# This file is documentation only. Apply the patch manually to your main.py.
