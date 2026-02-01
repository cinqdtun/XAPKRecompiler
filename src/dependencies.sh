#!/bin/bash

APKTOOL_VERSION="2.9.3"
JARSIGNER_VERSION="1.3.0"
APKTOOL_URL="https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_$APKTOOL_VERSION.jar"
JARSIGNER_URL="https://github.com/patrickfav/uber-apk-signer/releases/download/v$JARSIGNER_VERSION/uber-apk-signer-$JARSIGNER_VERSION.jar"
APKTOOL_PATH="./apktool.jar"
JARSIGNER_PATH="./jarsigner.jar"

if [ ! -f "$APKTOOL_PATH" ]; then
	echo "Downloading apktool $APKTOOL_VERSION..."
	curl -L -o "$APKTOOL_PATH" "$APKTOOL_URL"
	if [ $? -eq 0 ]; then
		chmod +x "$APKTOOL_PATH"
		echo "Download complete: $APKTOOL_PATH"
	else
		echo "Download failed."
		exit 1
	fi
else
	echo "Error: apktool.jar already exists at $APKTOOL_PATH"
fi

if [ ! -f "$JARSIGNER_PATH" ]; then
	echo "Downloading jarsigner $JARSIGNER_VERSION..."
	curl -L -o "$JARSIGNER_PATH" "$JARSIGNER_URL"
	if [ $? -eq 0 ]; then
		chmod +x "$JARSIGNER_PATH"
		echo "Download complete: $JARSIGNER_PATH"
	else
		echo "Download failed."
		exit 1
	fi
else
	echo "Error: jarsigner.jar already exists at $JARSIGNER_PATH"
fi