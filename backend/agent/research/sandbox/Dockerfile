# Sandbox image for running agent-generated strategy code.
# No network at run time (enforced via `docker run --network none`), only the
# scientific Python stack. The backtest engine and datasets are bind-mounted
# read-only at run time, so they are NOT copied in here.
FROM python:3.12-slim

# Scientific stack only. Pinned-ish to keep the image reproducible.
# Use a domestic PyPI mirror — the default index times out in this environment.
RUN pip install --no-cache-dir \
        -i https://pypi.tuna.tsinghua.edu.cn/simple \
        pandas==2.2.* \
        numpy==1.26.* \
        pyarrow==16.*

# Non-root user — agent code must never run as root.
RUN useradd --create-home --uid 1000 sandbox
USER sandbox
WORKDIR /work

# Default command is overridden by the runner; kept for manual testing.
CMD ["python", "-c", "print('sandbox ready')"]
