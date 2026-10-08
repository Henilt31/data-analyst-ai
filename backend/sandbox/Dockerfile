FROM python:3.12-slim

RUN useradd -m -d /workspace sandboxuser
WORKDIR /workspace

RUN pip install --no-cache-dir pandas numpy scipy matplotlib seaborn

COPY run_analysis.sh /workspace/run_analysis.sh
RUN chmod +x /workspace/run_analysis.sh

USER sandboxuser

ENTRYPOINT ["/workspace/run_analysis.sh"]
