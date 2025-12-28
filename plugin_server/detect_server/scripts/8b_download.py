from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Qwen/Qwen3-8B",
    cache_dir="/home/wb0zhang1/detect_server/data/transformers_cache/hub",
    resume_download=True,
    local_dir_use_symlinks=False,
    max_workers=16
)
