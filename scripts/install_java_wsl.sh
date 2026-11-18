#!/usr/bin/env bash
set -e

mkdir -p /opt/java /var/tmp/setup
cd /var/tmp/setup

echo "=== Downloading Eclipse Temurin OpenJDK 8 ==="
curl -fSL -o openjdk8.tar.gz "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u432-b06/OpenJDK8U-jdk_x64_linux_hotspot_8u432b06.tar.gz"
curl -fSL -o openjdk8.tar.gz.sha256.txt "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u432-b06/OpenJDK8U-jdk_x64_linux_hotspot_8u432b06.tar.gz.sha256.txt"

EXPECTED_SHA=$(awk '{print $1}' openjdk8.tar.gz.sha256.txt)
ACTUAL_SHA=$(sha256sum openjdk8.tar.gz | awk '{print $1}')

echo "Expected SHA-256: ${EXPECTED_SHA}"
echo "Actual SHA-256:   ${ACTUAL_SHA}"

if [ "${EXPECTED_SHA}" != "${ACTUAL_SHA}" ]; then
  echo "CHECKSUM MISMATCH! ABORTING."
  exit 1
fi

echo "Checksum verified successfully!"
rm -rf /opt/java/jdk8
tar -xzf openjdk8.tar.gz -C /opt/java/
EXTRACTED_DIR=$(find /opt/java -maxdepth 1 -mindepth 1 -type d -name "jdk8*" | head -n 1)
mv "${EXTRACTED_DIR}" /opt/java/jdk8

echo "=== Verifying Java in WSL2 ==="
/opt/java/jdk8/bin/java -version
/opt/java/jdk8/bin/javac -version
echo "Java installation complete."

