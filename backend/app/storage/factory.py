from app.storage.local_storage import LocalStorage


def build_storage(config):
    backend = config.get("STORAGE_BACKEND", "local")
    if backend == "local":
        return LocalStorage(base_path=config["LOCAL_STORAGE_PATH"], secret_key=config["SECRET_KEY"])
    if backend == "s3":
        # S3Storage intentionally not implemented in this sandbox build —
        # no AWS credentials/network access available to test against.
        # Swapping in a real S3Storage(BaseStorage) implementation here
        # is the only change needed; every caller already goes through
        # this factory and the BaseStorage interface.
        raise NotImplementedError(
            "S3Storage is not implemented yet — set STORAGE_BACKEND=local for now"
        )
    raise ValueError(f"Unknown STORAGE_BACKEND: {backend}")
