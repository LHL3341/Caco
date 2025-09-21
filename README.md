<p align="center">
<h1 align="center">Scaling Code-Assisted Chain-of-Thoughts and Instructions for Model Reasoning</h1>

<p align="center">
    <a href=""><img src="https://img.shields.io/badge/📄-Paper-red"></a>
    <a href="https://github.com/LHL3341/Caco/blob/main/LICENSE"><img src="https://img.shields.io/github/license/LHL3341/Caco"></a>
    <a href=""><img src="https://img.shields.io/badge/🤗 HuggingFace-Data & Models-green"></a>
</p>

🎉🎉: Caco is accepted Neurips 2026.
We introduce Caco, a code-driven framework for generating diverse and verifiable reasoning data at scale. Unlike conventional augmentation methods that only rewrite problems, Caco leverages executable code-based chains of thought (Code CoTs) to synthesize new problems and solutions with guaranteed correctness.

Caco implements this through three key stages:

1. Unifying Code CoT, collecting diverse seed reasoning traces from both mathematical and algorithmic problems, and converting them into a standardized executable format.

2. Scaling Code CoT, training a dedicated code generator that not only expands the dataset but also realizes Pattern-level Augmentation by restructuring reasoning logic (e.g., decomposition, reformulation, alternative solution paths).

3. Instruction Reversing, back-translating code into natural language problems with contextual and stylistic variations, followed by natural language CoT solution generation dual verification for correctness.

![](imgs/overview.png)

Caco yields 1.3M validated problem–solution pairs in under 55 GPU hours using only open-source models. Models trained on Caco data achieve consistent improvements across mathematics, logic puzzles, scientific QA, and code reasoning, surpassing strong baselines and demonstrating broad cross-domain generalization.

We release the Caco dataset and three Caco models fine-tuned on this dataset.

| Dataset/Model | MATH | CollegeMath | DeepMind-Mathematics | HuggingFace🤗 |
| - | :-: | :-: | :-: | :-: |
| Caco1.3M | - | - | - | [link]() |
| DeepSeekMath-7B-Caco | 53.4 | 39.8 | 65.8 | [link]() |
| Qwen2.5-7B-Caco | 41.6 | 24.3 | 39.2 | [link]() |
| Llama3-8B-Caco | 46.5 | 27.9 | 43.4 | [link]() |

## 🎯 Quick Start
Install the dependencies:

```bash
conda create -n mathfusion python=3.10
conda activate mathfusion
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cu121
# Install LLaMA-Factory
git clone https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
git checkout v0.9.1
pip install transformers==4.46.1 accelerate==0.34.2 deepspeed==0.15.4
pip install -e ".[torch,metrics]"
# Install packages for evaluation
pip install flash-attn --no-build-isolation
pip install sympy==1.12.1 antlr4-python3-runtime==4.11.1 pebble word2number boto3 triton==2.3.1 ipython
pip install vllm==0.5.3.post1
# Install latex2sympy
cd ../evaluation/latex2sympy
pip install -e .
cd ..
# Install dart-math evaluation
pip install -e .
```

## 🤖 Training
Our training codes depend on [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory).


## 📊 Evaluation

## Citation
If you find our code, model, or data are useful, please kindly cite our [paper]():
```

```
