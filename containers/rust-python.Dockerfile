FROM rust:latest as builder

RUN cargo install drug-extraction-cli



FROM python:3.10 

RUN python3 -m pip install pipx
RUN python3 -m pipx ensurepath
RUN pipx install de-workflow

COPY --from=builder /usr/local/cargo/bin/extract-drugs /usr/bin/extract-drugs

CMD ["bash"]
