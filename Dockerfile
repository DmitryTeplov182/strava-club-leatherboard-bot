
FROM python:3.11-slim


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99


WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm-dev \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxss1 \
    libxcb-dri3-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    xdg-utils \
    libu2f-udev \
    xvfb \
    x11vnc \
    fluxbox \
    && rm -rf /var/lib/apt/lists/*


RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable=131.0.6778.139-1 && rm -rf /var/lib/apt/lists/*


COPY . /app


RUN pip install --no-cache-dir -r /app/requirements.txt


RUN mkdir -p /root/.vnc && x11vnc -storepasswd "your_vnc_password" /root/.vnc/passwd


EXPOSE 5900


CMD /bin/bash -c "\
    Xvfb :99 -screen 0 1920x1080x24 & \
    fluxbox & \
    x11vnc -display :99 -rfbauth /root/.vnc/passwd -forever -shared -rfbport 5900 -bg -o /var/log/x11vnc.log & \
    python tg.py"
