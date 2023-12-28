#! /bin/bash
cargo build --release
cargo bundle --release
mkdir target/release/bundle/osx/LeafyHollows.app/Contents/Library
cp target/release/libSDL2-2.0.0.dylib target/release/bundle/osx/LeafyHollows.app/Contents/Library
install_name_tool -change @rpath/libSDL2-2.0.0.dylib @executable_path/../Library/libSDL2-2.0.0.dylib target/release/bundle/osx/LeafyHollows.app/Contents/MacOS/main