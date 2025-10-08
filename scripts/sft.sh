#!/bin/bash

conda activate caco
cd ./LLaMA-Factory

START_TIME=`date +%Y%m%d-%H:%M`

N_EPOCH=3
model_names=(
    "deepseek-ai/deepseek-math-7b-base"
    "Qwen/Qwen2.5-Math-7B"
)
deepspeed_configs=(
    "examples/deepspeed/ds_z2_config.json"
)
data_paths=(
    caco
)
template="alpaca1"

for i in "${!model_names[@]}"; do
    base_model_name=${model_names[$i]}
    ds_config=${deepspeed_configs[0]}
    for dataset_name in "${data_paths[@]}"; do
        # pkill sft_lr
        MASTER_PORT=31692 llamafactory-cli train \
            --deepspeed ${ds_config}  \
            --stage sft \
            --do_train True \
            --use_fast_tokenizer \
            --flash_attn fa2 \
            --model_name_or_path ${base_model_name} \
            --dataset ${dataset_name} \
            --template ${template} \
            --seed 42 \
            --finetuning_type full \
            --preprocessing_num_workers 16 \
            --output_dir sft-models/${base_model_name}/${dataset_name}_${N_EPOCH}epoch/${START_TIME} \
            --warmup_ratio 0.03 \
            --weight_decay 0.1 \
            --per_device_train_batch_size 8 \
            --gradient_accumulation_steps 2 \
            --ddp_timeout 280000000 \
            --learning_rate 5e-6 \
            --lr_scheduler_type cosine \
            --logging_steps 5 \
            --cutoff_len 4096 \
            --save_steps 10000000 \
            --plot_loss True \
            --num_train_epochs ${N_EPOCH} \
            --bf16 True \
            --save_only_model \
            --dataset_dir data \
            --report_to none \
            --use_liger_kernel 
    done
done