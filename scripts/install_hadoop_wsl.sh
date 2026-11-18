#!/usr/bin/env bash
set -e

mkdir -p /opt/hadoop /var/tmp/hadoop_setup
cd /var/tmp/hadoop_setup

echo "=== Downloading Apache Hadoop 3.3.6 and SHA-512 Checksum ==="
curl -fSL -o hadoop-3.3.6.tar.gz "https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz"
curl -fSL -o hadoop-3.3.6.tar.gz.sha512 "https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz.sha512"

echo "=== Cryptographic SHA-512 Checksum Verification ==="
# Apache sha512 file format: "SHA512 (hadoop-3.3.6.tar.gz) = <hash>" or "<hash>  hadoop-3.3.6.tar.gz"
EXPECTED_HASH=$(tr -d ' \t\n\r' < hadoop-3.3.6.tar.gz.sha512 | sed -E 's/.*=//' | tr '[:upper:]' '[:lower:]')
ACTUAL_HASH=$(sha512sum hadoop-3.3.6.tar.gz | awk '{print $1}' | tr '[:upper:]' '[:lower:]')

echo "Expected SHA-512: ${EXPECTED_HASH}"
echo "Actual SHA-512:   ${ACTUAL_HASH}"

if [ "${EXPECTED_HASH}" != "${ACTUAL_HASH}" ]; then
  echo "CHECKSUM VERIFICATION FAILED! Aborting installation."
  exit 1
fi

echo "SHA-512 Checksum VERIFIED SUCCESSFULLY!"

echo "=== Extracting Hadoop 3.3.6 ==="
rm -rf /opt/hadoop/hadoop-3.3.6
tar -xzf hadoop-3.3.6.tar.gz -C /opt/hadoop/

# Setup directories and permissions
mkdir -p /var/hadoop/data/dfs/name /var/hadoop/data/dfs/data /var/hadoop/logs
chown -R naveen:naveen /opt/hadoop /var/hadoop

echo "Hadoop extracted to /opt/hadoop/hadoop-3.3.6 successfully."
rm -rf /var/tmp/hadoop_setup

