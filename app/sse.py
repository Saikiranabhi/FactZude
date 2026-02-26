from fastapi.responses import StreamingResponse
import asyncio

async def event_stream(data: dict):
    for key, value in data.items():
        yield f"data: {key}: {value}\n\n"
        await asyncio.sleep(0.5)

def sse_response(data: dict):
    return StreamingResponse(event_stream(data), media_type="text/event-stream")