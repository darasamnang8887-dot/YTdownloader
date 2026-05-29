[app]

# (str) Title of your application
title = YT Downloader

# (str) Package name
package.name = ytdownloader

# (str) Package domain (needed for android packaging)
package.domain = org.youmeas

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let's include py files, png logo, and config files)
source.include_exts = py,png,json,txt

# (list) List of exclusions using pattern matching
source.exclude_exts = spec,spec-backup,db,sqlite3

# (list) List of directory exclusions
source.exclude_dirs = templates,static,downloads,build,dist,__pycache__,.git,.github

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# We include python3, Kivy, yt-dlp, openssl for HTTPS, requests, pyjnius, and supporting libraries
requirements = python3==3.11,kivy==2.3.0,openssl,requests,urllib3,certifi,idna,charset-normalizer,pyjnius

# (str) Supported orientations (portrait, landscape or all)
orientation = portrait

# (bool) Use fullscreen or not
fullscreen = 1

# (list) Permissions required by the app.
# Android 15+ Scoped Storage doesn't require storage permissions for app-specific directories.
# We only require INTERNET to download videos.
android.permissions = INTERNET

# (int) Target Android API Level (Android 15 is API 35)
android.api = 35

# (int) Minimum API Level supported (Standard fallback for Kivy is 21+)
android.minapi = 21

# (str) Android NDK version to use (NDK r26b is recommended for API 35 building)
android.ndk = 26b

# (list) The Android Architectures to build for (Modern Android devices use arm64-v8a or armeabi-v7a)
android.archs = armeabi-v7a, arm64-v8a

# (str) Icon of the application (using the premium logo.png in workspace)
icon.filename = logo.png

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/logo.png

# (str) Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# (str) Android app theme
android.theme = @android:style/Theme.NoTitleBar.Fullscreen

# (bool) Enable Android logcat filter (cleans Kivy logs)
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a symlink
# android.copy_libs = 1

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
