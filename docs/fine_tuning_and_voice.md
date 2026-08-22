# 🧪 Fine-Tuning, Synthetic Datasets & Custom Voice Pipeline

The Fine-Tuning subsystem (`gaming_ai.training`) provides tools to synthesize gaming dialogue datasets, train custom LoRA adapters using QLoRA 4-bit quantization on an 8 GB VRAM GPU, export to GGUF, and package custom Ollama models.

---

## 🏛️ Fine-Tuning Pipeline (Section 48 & 49 Compliance)

```
[ Curated Gaming Scenarios / Live Game Telemetry ]
                        │
                        ▼
       [ DatasetGenerator (ChatML JSONL) ]
                        │
                        ▼
       [ 4-bit QLoRA SFT Training (PyTorch / PEFT) ]
           (Optimized for RTX 3070 8GB VRAM)
                        │
                        ▼
            [ Saved LoRA Adapter ]
                        │
                        ▼
       [ export_ollama_modelfile ] ──► [ Ollama Modelfile ]
                                              │
                                              ▼
                             [ ollama create gaming-companion ]
```

---

## 🚀 1. Generating Training Data

Generate synthetic gaming dialogue formatted for ChatML / Hugging Face SFT:
```python
from gaming_ai.training.dataset_generator import DatasetGenerator

generator = DatasetGenerator()
samples = generator.generate_seed_dataset()
path = generator.export_jsonl(samples, output_file="data/training/gaming_dataset.jsonl")
print(f"Dataset generated at {path}")
```

---

## ⚡ 2. 8 GB VRAM QLoRA Hyperparameters

In [`train_lora.py`](file:///e:/MohamedWorks/AI/gaming_ai/training/train_lora.py):
* **Base Model**: `meta-llama/Llama-3.2-3B-Instruct` or `Qwen/Qwen2.5-3B-Instruct`
* **Quantization**: 4-bit NormalFloat (`BitsAndBytesConfig(load_in_4bit=True)`)
* **LoRA Rank & Alpha**: $r = 16, \alpha = 32$
* **Optimizer**: `paged_adamw_8bit` with gradient checkpointing
* **Peak VRAM during training**: $\sim 5.4\text{ GB}$ (safely fits within 8 GB VRAM!)

---

## 📦 3. Packaging into Ollama

Generate an Ollama `Modelfile` and create the local model:
```bash
python -c "from gaming_ai.training.export_gguf import export_ollama_modelfile; export_ollama_modelfile()"
ollama create gaming-companion -f Modelfile
```
In `config.yaml`:
```yaml
ai:
  model: "gaming-companion"
```
