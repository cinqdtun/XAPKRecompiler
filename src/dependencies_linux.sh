#!/bin/bash

APKTOOL_VERSION="2.9.3"
JARSIGNER_VERSION="1.3.0"
APKTOOL_URL="https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_$APKTOOL_VERSION.jar"
JARSIGNER_URL="https://github.com/patrickfav/uber-apk-signer/releases/download/v$JARSIGNER_VERSION/uber-apk-signer-$JARSIGNER_VERSION.jar"
CMD_TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-14742923_latest.zip"
APKTOOL_PATH="./apktool.jar"
JARSIGNER_PATH="./jarsigner.jar"
ANDROID_SDK_PATH="./android_SDK"
CMD_TOOLS_PATH="./cmd-tools.zip"
SDK_MANAGER_PATH="$ANDROID_SDK_PATH/cmdline-tools/latest/bin/sdkmanager"

mkdir dependencies
cd dependencies

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

if [ ! -f $ANDROID_SDK_PATH ]; then
	echo "Downloading latest Android SDK..."
	curl -L -o "$CMD_TOOLS_PATH" "$CMD_TOOLS_URL"
	if [ $? -eq 0 ]; then
		mkdir -p "$ANDROID_SDK_PATH/cmdline-tools/latest"
		unzip -q "$CMD_TOOLS_PATH" -d "."
		rm -rf $CMD_TOOLS_PATH
		mv ./cmdline-tools/* "$ANDROID_SDK_PATH/cmdline-tools/latest"
		rm -rf cmdline-tools
		yes | $SDK_MANAGER_PATH --sdk_root=$ANDROID_SDK_PATH "build-tools;36.1.0-rc1"
		yes | $SDK_MANAGER_PATH --sdk_root=$ANDROID_SDK_PATH "platform-tools"
		echo "Download complete: $ANDROID_SDK_PATH"
	else
		echo "Download failed."
		exit 1
	fi
else
	echo "Error: Android SDK already exists at $ANDROID_SDK_PATH"
fi