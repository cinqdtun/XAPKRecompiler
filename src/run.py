import os
import re
import sys
import json
import shutil
import zipfile
import argparse 
import tempfile
import subprocess

NETWORK_CONFIG_PATH = "./configs/network_security_config.xml"
APKTOOL_JAR = "./dependencies/apktool.jar"
SIGNER_JAR = "./dependencies/jarsigner.jar"
ADB_PATH = "./dependencies/android_SDK/platform-tools/adb"
ZIPALIGN_PATH = "./dependencies/android_SDK/build-tools/36.1.0-rc1/zipalign"
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
	parser = argparse.ArgumentParser(description='Recompile XAPK with optional patches')
	parser.add_argument('input_xapk', help='Input XAPK file')
	parser.add_argument('--network-fix', action='store_true', help='Apply network security config patch')
	parser.add_argument('--extract-native-libs', action='store_true', help='Set extractNativeLibs to true')
	parser.add_argument('--pause', action='store_true', help='Pause after applying patches for manual patches before rebuilding')
	parser.add_argument('--install', action='store_true', help='Install patched APKs to connected ADB device after packaging')

	args = parser.parse_args()
	input_xapk = args.input_xapk
	temp_dir = tempfile.TemporaryDirectory()

	# need to rework this
	if not shutil.which("java"):
		print("Error: Java not found.", file=sys.stderr)
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
					apk_id = item.get('id')
					if apk_id == 'base':
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

	android_manifest_path = os.path.join(base_decomp_dir, "AndroidManifest.xml")
	with open(android_manifest_path, 'r') as f:
		content = f.read() # Read android manifest

	# Patch 1: Adding network config location if does not exist
	if args.network_fix:
		shutil.copy(NETWORK_CONFIG_PATH, os.path.join(res_xml_path, "network_security_config.xml")) # Copy network config
		if "android:networkSecurityConfig" not in content:
			if "<application" in content:
				content = content.replace("<application", '<application android:networkSecurityConfig="@xml/network_security_config"', 1)
				print(" Patch: Added Network Security Config to manifest")
	
	# Patch 2: Patching extractNativeLibs to true
	if args.extract_native_libs:
		if "android:extractNativeLibs" in content:
			content = re.sub(r'android:extractNativeLibs="[^"]*"', 'android:extractNativeLibs="true"', content)
			print(" Patch: Patched extractNativeLibs to true")
		else:
			if "<application" in content:
				content = content.replace("<application", '<application android:extractNativeLibs="true"', 1)
				print(" Patch: Added extractNativeLibs to manifest")

	with open(android_manifest_path, 'w') as f:
		f.write(content)
	
	if args.pause:
		print(f" Temporary folder path: {temp_dir.name}")
		input(" Patch has been applied press any key to continue...")
	
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
			run([ZIPALIGN_PATH, "-p", "-f", "4", apk_path, aligned_apk_path])
			shutil.move(aligned_apk_path, apk_path)

	run(["java", "-jar", SIGNER_JAR, "--apks", temp_dir.name, "--overwrite", "--skipZipAlign", "--allowResign"])
	
	for filename in os.listdir(temp_dir.name):
		if filename.endswith(".idsig"):
			os.remove(os.path.join(temp_dir.name, filename))

	# 7. Packaging
	output_xapk = input_xapk.replace(".xapk", "_patched.xapk")
	print(f"--- 7. Packaging into {output_xapk} ---")
	
	with zipfile.ZipFile(output_xapk, 'w', zipfile.ZIP_DEFLATED) as z:
		for root, dirs, files in os.walk(temp_dir.name):
			for file in files:
				file_path = os.path.join(root, file)
				z.write(file_path, os.path.relpath(file_path, temp_dir.name))

	print(f"Success! Output file at: {output_xapk}")
	# 8. Install
	apk_files = [os.path.join(temp_dir.name, f) for f in os.listdir(temp_dir.name) if f.endswith('.apk')]

	if (apk_files and args.install):
		print(f"--- 8. Installing patched APKs ---")
		run([ADB_PATH, "install-multiple"] + apk_files)
		print(" Installation complete.")

	shutil.rmtree(temp_dir.name)
	
	
if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		print(e)
		errorExit()
