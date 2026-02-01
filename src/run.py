import os
import re
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess

NETWORK_CONFIG_PATH = "./configs/network_security_config.xml"
APKTOOL_JAR = "./apktool.jar"
SIGNER_JAR = "./jarsigner.jar"
BASE_APK_NOT_FOUND_STR = "Error: Base APK not found"
CMD_FAILED_STR = "Error: running command:"

temp_dir = None

def errorExit():
	if temp_dir:
		temp_dir.cleanup()
	sys.exit(1)

def run(cmd):
	try:
		subprocess.check_call(cmd, shell=False)
	except subprocess.CalledProcessError as e:
		print(f"{CMD_FAILED_STR} {' '.join(cmd)}", file=sys.stderr)
		errorExit()

def main():
	if len(sys.argv) < 2:
		print(f"Usage: python3 {sys.argv[0]} <file.xapk>", file=sys.stderr)
		sys.exit(1)

	input_xapk = sys.argv[1]
	temp_dir = tempfile.TemporaryDirectory()

	# need to rework this
	if not shutil.which("java"):
		print("Error: Java not found.", file=sys.stderr)
		errorExit()
	if not shutil.which("zipalign"): 
		print("Error: zipalign not found.", file=sys.stderr)
		errorExit()
	
	# 1. Extracting XAPK
	print(f"--- 1. Extracting {input_xapk} ---")
	with zipfile.ZipFile(input_xapk, 'r') as z:
		z.extractall(temp_dir.name)

	# 2. Identify Base APK using manifest
	print("--- 2. Identifying Base APK using manifest ---")
	manifest_path = os.path.join(temp_dir.name, "manifest.json")
	base_apk = None

	if os.path.exists(manifest_path):
		try:
			with open(manifest_path, 'r') as f:
				data = json.load(f)
				for item in data.get('split_apks', []):
					if item.get('id') == 'base':
						base_apk = item.get('file')
						break
		except:
			pass
	if not base_apk:
		print(BASE_APK_NOT_FOUND_STR, file=sys.stderr)
		errorExit(temp_dir.name)

	print(f" Found base apk: {base_apk}")
	base_apk_path = os.path.join(temp_dir.name, base_apk)
	base_decomp_dir = os.path.join(temp_dir.name, "base")

	# 3. Decompile Base APK
	print("--- 3. Decompiling Base APK ---")
	run(["java", "-jar", APKTOOL_JAR, "d", base_apk_path, "-o", base_decomp_dir, "-f"])

	# 4. Inject newtork fix into app
	print("--- 4. Inject network fix into app ---")
	res_xml_path = os.path.join(base_decomp_dir, "res", "xml")
	os.makedirs(res_xml_path, exist_ok=True) # creating DIR if does not exist

	shutil.copy(NETWORK_CONFIG_PATH, os.path.join(res_xml_path, "network_security_config.xml")) # Copy network config

	android_manifest_path = os.path.join(base_decomp_dir, "AndroidManifest.xml")
	with open(android_manifest_path, 'r') as f:
		content = f.read() # Read android manifest

	# Patch 1: Adding network config location if does not exist
	if "android:networkSecurityConfig" not in content:
		if "<application" in content:
			content = content.replace("<application", '<application android:networkSecurityConfig="@xml/network_security_config"', 1)
			print(" Patch: Added Network Security Config to manifest")
	
	# Patch 2: Patching extractNativeLibs to true
	if "android:extractNativeLibs" in content:
		content = re.sub(r'android:extractNativeLibs="[^"]*"', 'android:extractNativeLibs="true"', content)
		print(" Patch: Patched extractNativeLibs to true")
	else:
		if "<application" in content:
			content = content.replace("<application", '<application android:extractNativeLibs="true"', 1)
			print(" Patch: Added extractNativeLibs to manifest")

	with open(android_manifest_path, 'w') as f:
		f.write(content)
	
	print(f"Temporary folder path: {temp_dir.name}")
	input("Patch has been applied press any key to continue...")
	
	# 5. Recompiling Base APK
	print("--- 5. Recompiling Base APK ---")
	run(["java", "-jar", APKTOOL_JAR, "b", base_decomp_dir, "-o", base_apk_path])
	shutil.rmtree(base_decomp_dir)

	# 6. Aligning / Signing
	print("--- 6. Aligning / Signing ---")
	for filename in os.listdir(temp_dir.name):
		if filename.endswith(".apk"):
			apk_path = os.path.join(temp_dir.name, filename)
			aligned_apk_path = apk_path + ".aligned"
			run(["zipalign", "-p", "-f", "4", apk_path, aligned_apk_path])
			shutil.move(aligned_apk_path, apk_path)

	run(["java", "-jar", SIGNER_JAR, "--apks", temp_dir.name, "--overwrite", "--skipZipAlign"])

	# 7. Packaging
	output_xapk = input_xapk.replace(".xapk", "_patched.xapk")
	print(f"--- 7. Packaging into {output_xapk} ---")
	
	with zipfile.ZipFile(output_xapk, 'w', zipfile.ZIP_DEFLATED) as z:
		for root, dirs, files in os.walk(temp_dir.name):
			for file in files:
				file_path = os.path.join(root, file)
				z.write(file_path, os.path.relpath(file_path, temp_dir.name))

	shutil.rmtree(temp_dir.name)
	print(f"Success! Output file at: {output_xapk}")
	
if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		print(e)
		errorExit()
