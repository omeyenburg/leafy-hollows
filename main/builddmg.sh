#!/bin/bash
mkdir -p dist/dmg
rm -r dist/dmg/*
cp -r "dist/Hello World.app" dist/dmg
test -f "dist/Hello World.dmg" && rm "dist/Hello World.dmg"
create-dmg \
  --volname "Hello World" \
  --volicon "icon/icon.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "Hello World.app" 175 120 \
  --hide-extension "Hello World.app" \
  --app-drop-link 425 120 \
  "dist/Hello World.dmg" \
  "dist/dmg/"