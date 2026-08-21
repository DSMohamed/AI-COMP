# 🧠 Models & Providers

The application uses an extensible provider architecture that separates model inference from business logic, allowing new local backends (Ollama, llama.cpp, vLLM, TensorRT-LLM) or test mocks to be added seamlessly.

---

## 🏛️ Provider Architecture

All LLM providers inherit from `BaseLLMProvider` in [`gaming_ai.models.provider`](../gaming_ai/models/provider.py):

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def is_available(self) -> bool:
        """Check whether the model provider and endpoint are reachable."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 250,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a complete text response asynchronously."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 250,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream generated response tokens asynchronously."""
        pass
```

---

## 🦙 Ollama Provider (`gaming_ai.models.ollama`)

The `OllamaProvider` connects asynchronously to local Ollama instances:
* **Default Host**: `http://127.0.0.1:11434`
* **Default Model**: `llama3.2:3b`
* **API Endpoints**:
  * `GET /api/tags`: Model availability and health verification.
  * `POST /api/chat`: Non-streaming and streaming chat completions.

### Recommended Models for RTX 3070 8GB:

| Model | Size (Quant) | Generation Speed | Best For |
|---|---|---|---|
| `llama3.2:3b` | 2.0 GB (Q4_K_M) | **~128 tok/s** | Real-time gaming companion, witty banter, ultra-low latency |
| `qwen2.5-coder:7b` | 4.7 GB (Q4_K_M) | **~55 tok/s** | Complex strategic reasoning, build crafting, in-depth mechanics |
| `deepseek-r1:8b` | 5.2 GB (Q4_K_M) | **~48 tok/s** | Step-by-step tactical calculations |

---

## 🧪 Mock Provider (`gaming_ai.models.provider.MockLLMProvider`)

For offline testing, CI environments, and unit testing without requiring an active Ollama instance:

```python
from gaming_ai.models.provider import MockLLMProvider, Message

provider = MockLLMProvider(canned_response="BRO THAT WAS CLUTCH!")
response = await provider.generate([Message("user", "Did I win?")])
print(response.content)  # "BRO THAT WAS CLUTCH!"
```

---

## 🛠️ How to Add a Custom Provider

To add a new provider (e.g. `LlamaCppProvider`):

1. Create `gaming_ai/models/llamacpp.py`.
2. Inherit from `BaseLLMProvider`.
3. Implement `is_available()`, `generate()`, and `generate_stream()`.
4. Register the new provider in `gaming_ai/models/__init__.py` and the agent factory.
