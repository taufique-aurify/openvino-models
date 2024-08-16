import os

BINARIES_PATHS = [
    *os.environ.get("OPENVINO_LIB_PATHS", '').split(";"),
    os.path.join(os.path.join(LOADER_DIR, "../../../"), "opencv/bin")
] + BINARIES_PATHS
