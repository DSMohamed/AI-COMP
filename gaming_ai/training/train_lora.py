"""LoRA / QLoRA fine-tuning configuration and script builder for gaming companion LLMs."""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("gaming_ai.training.train_lora")


@dataclass
class LoRATrainingConfig:
    """Hyperparameters optimized for fine-tuning on an 8 GB VRAM GPU."""
    base_model_name: str = "meta-llama/Llama-3.2-3B-Instruct"
    dataset_path: str = "data/training/dataset.jsonl"
    output_dir: str = "models/gaming_companion_lora"
    max_seq_length: int = 512
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )
    learning_rate: float = 2e-4
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    num_train_epochs: int = 3
    use_4bit_quantization: bool = True  # QLoRA for 8GB VRAM
    gradient_checkpointing: bool = True


def build_training_pipeline(config: Optional[LoRATrainingConfig] = None) -> str:
    """
    Generate a complete, self-contained PyTorch / Hugging Face SFT training script.
    """
    cfg = config or LoRATrainingConfig()
    
    script_content = f'''"""
Standalone QLoRA Fine-Tuning Script for Local AI Gaming Companion
Target GPU: NVIDIA RTX 3070 8GB (using 4-bit NormalFloat QLoRA)
"""

import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer

def main():
    print("🚀 Starting Gaming Companion QLoRA Fine-Tuning...")
    
    model_id = "{cfg.base_model_name}"
    output_dir = "{cfg.output_dir}"
    dataset_file = "{cfg.dataset_path}"

    # 1. 4-bit Quantization Config for 8GB VRAM
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # 2. Load Base Model & Tokenizer
    print(f"Loading base model: {{model_id}}")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    # 3. LoRA Adapter Config
    peft_config = LoraConfig(
        r={cfg.lora_r},
        lora_alpha={cfg.lora_alpha},
        lora_dropout={cfg.lora_dropout},
        target_modules={cfg.target_modules},
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 4. Load Dataset
    print(f"Loading training data from {{dataset_file}}")
    dataset = load_dataset("json", data_files=dataset_file, split="train")

    # 5. Training Arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size={cfg.batch_size},
        gradient_accumulation_steps={cfg.gradient_accumulation_steps},
        learning_rate={cfg.learning_rate},
        num_train_epochs={cfg.num_train_epochs},
        logging_steps=10,
        save_strategy="epoch",
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        gradient_checkpointing={cfg.gradient_checkpointing},
        optim="paged_adamw_8bit",
        report_to="none",
    )

    # 6. SFT Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        dataset_text_field="messages",
        max_seq_length={cfg.max_seq_length},
        tokenizer=tokenizer,
        args=training_args,
    )

    print("⚡ Training in progress...")
    trainer.train()

    print(f"✅ Training completed! Saving LoRA adapter to {{output_dir}}")
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

if __name__ == "__main__":
    main()
'''
    return script_content
