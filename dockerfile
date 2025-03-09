FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    make \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn

COPY requirements.txt* ./

RUN pip install --no-cache-dir -r requirements.txt || echo "No requirements.txt found, skipping"

RUN pip install --no-cache-dir pre-commit

COPY . .

RUN mkdir -p theme

RUN chmod +x tools/*.sh 2>/dev/null || echo "No shell scripts to make executable"

ENTRYPOINT ["make"]

CMD ["all"]
