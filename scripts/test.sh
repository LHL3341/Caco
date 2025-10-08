
conda activate caco

cd ./evaluation_qwen

PROMPT_TYPE="cot-meta-math"

export DATA_NAME="gsm8k,math,mathmetics,olympiadbench,theoremqa"
export NUM_TEST_SAMPLE=-1


bash sh/eval.sh $PROMPT_TYPE $MODEL_NAME


# College Math
cd ./evaluation_dart
n_shots=0
DATASETS_LIST=(
  "mwpbench/college-math/test"
)

for DATASETS in ${DATASETS_LIST[@]}; do
  save_pre=outputs/${DATASETS////_}
  mkdir -p $save_pre
  save_path="${save_pre}/${RES_PATH}_${PROMPT_TYPE}_n${n_shots}_seed0.jsonl"
  echo $save_path

  set -x

  python run.py \
      --gen_save_path $save_path \
      --model_name_or_path "${MODEL_NAME}" \
      --datasets $DATASETS \
      --max_new_toks 2048 --temperature 0 \
      --prompt_template $PROMPT_TYPE \
      --n_shots $n_shots \
      --inf_seed 0 \
      --max_n_trials 1

  python print_metric.py --gen_save_path $save_path
  
done