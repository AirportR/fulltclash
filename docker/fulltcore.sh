#!/bin/bash

rm -f /app/bin/*

ORIGIN_AMD64_URL=https://github.com/AirportR/FullTCore/releases/download/v1.0/FullTCore_1.0_linux_amd64.tar.gz
META_AMD64_URL=https://github.com/AirportR/FullTCore/releases/download/v1.1-meta/FullTCore_1.1-meta_linux_amd64.tar.gz
ORIGIN_ARM64_URL=https://github.com/AirportR/FullTCore/releases/download/v1.0/FullTCore_1.0_linux_arm64.tar.gz
META_ARM64_URL=https://github.com/AirportR/FullTCore/releases/download/v1.1-meta/FullTCore_1.1-meta_linux_arm64.tar.gz

arch=$(arch)

if [[ $arch == "x86_64" || $arch == "x64" || $arch == "amd64" ]]; then
  arch="amd64"
  wget -O /app/bin/FullTCore_origin.tar.gz ${ORIGIN_AMD64_URL} > /dev/null 2>&1
  wget -O /app/bin/FullTCore_meta.tar.gz ${META_AMD64_URL} > /dev/null 2>&1
elif [[ $arch == "aarch64" || $arch == "arm64" ]]; then
  arch="arm64"
  wget -O /app/bin/FullTCore_origin.tar.gz ${ORIGIN_ARM64_URL} > /dev/null 2>&1
  wget -O /app/bin/FullTCore_meta.tar.gz ${META_ARM64_URL} > /dev/null 2>&1
fi

tar -C /app/bin/ -xvzf /app/bin/FullTCore_origin.tar.gz
mv /app/bin/FullTCore /app/bin/fulltclash-origin

tar -C /app/bin/ -xvzf /app/bin/FullTCore_meta.tar.gz
mv /app/bin/FullTCore /app/bin/fulltclash-meta

find /app/bin/* | egrep -v "fulltclash-origin|fulltclash-meta" | xargs rm -f

chmod +x /app/bin/fulltclash-origin
chmod +x /app/bin/fulltclash-meta

echo "架构: ${arch}下载FullTCore完成"