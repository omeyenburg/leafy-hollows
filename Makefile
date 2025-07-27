.PHONY: build dmg clean

build:
	pyinstaller build.spec

dmg:
	@mkdir -p dist/dmg
	@rm -rf dist/dmg/*
	@cp -r dist/LeafyHollows.app dist/dmg
	@if [ -f dist/LeafyHollows.dmg ]; then rm dist/LeafyHollows.dmg; fi
	create-dmg \
	  --volname LeafyHollows \
	  --volicon icon/icon.icns \
	  --window-pos 200 120 \
	  --window-size 600 300 \
	  --icon-size 100 \
	  --icon LeafyHollows.app 175 120 \
	  --hide-extension LeafyHollows.app \
	  --app-drop-link 425 120 \
	  dist/LeafyHollows.dmg \
	  dist/dmg/

clean:
	rm -rf build dist
