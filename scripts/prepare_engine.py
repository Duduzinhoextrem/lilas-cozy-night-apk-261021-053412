#!/usr/bin/env python3
"""Embed Lila's Cozy Night in CPsP Codename Engine Mobile legacy source.

The source is downloaded separately and must match the pinned engine revision.
Designed for a private test build. No claims of runtime compatibility.
"""
import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
MOD_ID = "lilas-cozy-night"
PACKAGE = "com.dudz.lilas.cozy.night"
ENGINE_REV = "4af5529d60ebf2599372cd95463acfd6707c5cdd"


def patch_once(content, before, after, filename):
    count=content.count(before)
    if count != 1:
        raise RuntimeError(f"{filename}: expected 1 occurrence of {before!r}, found {count}; engine may have changed")
    return content.replace(before, after, 1)


def ensure_zip_safe(z):
    for f in z.infolist():
        name=f.filename
        p=Path(name)
        if name.startswith('/') or '..' in p.parts or '\\' in name:
            raise ValueError('Unsafe zip member: '+name)
        if f.file_size > 60*1024*1024:
            raise ValueError('Unusually large zip member: '+name)


def embed_mod(engine):
    payload=HERE/'mod/lilas-cozy-night-mobile.zip'
    if not payload.exists():
        raise FileNotFoundError(payload)
    mod_path=engine/'mods'/MOD_ID
    mod_path.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(payload) as z:
        ensure_zip_safe(z)
        names=set(z.namelist())
        must={'data/config/modpack.ini','data/config/freeplaySonglist.txt','data/states/CozyMenu.hx','songs/beathoven/meta.json'}
        missing=must-names
        if missing: raise RuntimeError('Missing files in mod: '+str(sorted(missing)))
        for info in z.infolist():
            if info.is_dir(): continue
            target=mod_path/info.filename
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as inp, target.open('wb') as out:
                import shutil
                shutil.copyfileobj(inp,out)
        print(f'Embedded {len(z.infolist())} mod assets into {mod_path}')
    (engine/'mods/autoload.txt').write_text(MOD_ID+'\n',encoding='utf-8')


def patch_project_xml(engine):
    path=engine/'project.xml'
    src=path.read_text(encoding='utf-8')
    if 'title="Lila\'s Cozy Night"' in src:
        print('project.xml already customized')
        return
    for old,new in [
        ('title="Codename Engine"','title="Lila\'s Cozy Night"'),
        ('file="CodenameEngine"','file="LilasCozyNight"'),
        ('packageName="com.yoshman29.codenameengine"',f'packageName="{PACKAGE}"'),
        ('package="com.yoshman29.codenameengine"',f'package="{PACKAGE}"'),
        ('company="Yoshman29"','company="Dudz"'),
        ('<haxedef name="SAVE_PATH" value="CodenameEngine"/>','<haxedef name="SAVE_PATH" value="LilasCozyNight"/>'),
        ('<haxedef name="SAVE_NAME" value="save-default"/>','<haxedef name="SAVE_NAME" value="cozy-save"/>'),
        ('<haxedef name="SAVE_OPTIONS_PATH" value="CodenameEngine"/>','<haxedef name="SAVE_OPTIONS_PATH" value="LilasCozyNight"/>')
    ]:
        src=patch_once(src,old,new,'project.xml')
    if '<assets path=\'mods\' rename=\'mods\'' not in src:
        raise RuntimeError("The pinned engine's project.xml no longer packages mods assets")
    # The main Android icon has an override in the upstream port. Replace all icon paths.
    for name in ('icon16.png','icon32.png','icon64.png','iconOG.png','teaser.png'):
        src=src.replace('art/'+name,'art/cozy-icon.png')
    path.write_text(src,encoding='utf-8')
    art=engine/'art'
    art.mkdir(exist_ok=True)
    import shutil
    shutil.copyfile(HERE/'assets/lila-icon.png',art/'cozy-icon.png')


def patch_main(engine):
    """Put mod in app-owned directory before mod initialization.

    A bundled mods directory in APK isn't guaranteed to be the one ModsFolder
    reads on mobile, so copy it if the port has unpacked it to assetDirectory.
    """
    p=engine/'source/funkin/backend/system/Main.hx'
    src=p.read_text(encoding='utf-8')
    if 'COZY_APK_MOD_V1' in src:
        print('Main.hx already patched')
        return
    # Use sys filesystem functions only on mobile; the class already imports them for sys.
    src=patch_once(src,'\t\tMobileUtil.copyAssets();',
        '\t\tMobileUtil.copyAssets();\n'
        '\t\t#if android\n'
        '\t\tcozyEnsurePackagedMod();\n'
        '\t\t#end', 'Main.hx')
    # Always choose the bundled mod even if the user previously selected another mod.
    needle='\t\tModsFolder.switchMod(modToLoad.getDefault(Options.lastLoadedMod));'
    src=patch_once(src,needle,
        '\t\t#if android\n'
        '\t\tmodToLoad = "lilas-cozy-night"; // COZY_APK_MOD_V1\n'
        '\t\t#end\n'+needle,'Main.hx')
    # Add standalone helper inside the Main class before the fixWorkingDirectory method.
    anchor='\tpublic static function fixWorkingDirectory() {'
    helper="""\t#if android
\tprivate static function cozyEnsurePackagedMod():Void {
\t\tvar src = haxe.io.Path.addTrailingSlash(MobileUtil.getAssetDirectory()) + "mods/lilas-cozy-night";
\t\tvar dst = haxe.io.Path.addTrailingSlash(MobileUtil.getDirectory()) + "mods/lilas-cozy-night";
\t\tvar sentinel = dst + "/.cozy-apk-v1";
\t\tif (FileSystem.exists(sentinel)) return;
\t\tif (!FileSystem.exists(src) || !FileSystem.isDirectory(src)) {
\t\t\ttrace("COZY_APK source missing: " + src);
\t\t\treturn;
\t\t}
\t\ttry {
\t\t\tcozyCopyFolder(src, dst);
\t\t\tFile.saveContent(sentinel, "Lila's Cozy Night - bundled assets v1");
\t\t\ttrace("COZY_APK copied bundled mod to " + dst);
\t\t} catch (e:Dynamic) {
\t\t\ttrace("COZY_APK copy failed: " + Std.string(e));
\t\t}
\t}

\tprivate static function cozyCopyFolder(src:String, dst:String):Void {
\t\tif (!FileSystem.exists(dst)) FileSystem.createDirectory(dst);
\t\tfor (name in FileSystem.readDirectory(src)) {
\t\t\tvar input = haxe.io.Path.join([src, name]);
\t\t\tvar output = haxe.io.Path.join([dst, name]);
\t\t\tif (FileSystem.isDirectory(input)) cozyCopyFolder(input, output);
\t\t\telse File.copy(input, output);
\t\t}
\t}
\t#end

"""
    src=patch_once(src,anchor,helper+anchor,'Main.hx')
    p.write_text(src,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser(description='Integrate Lila mod in Codename Mobile engine sources')
    parser.add_argument('--engine',type=Path,required=True,help='Path to cloned CPsP CodenameEngine-Mobile at pinned revision')
    args=parser.parse_args()
    e=args.engine.resolve()
    if not (e/'project.xml').is_file() or not (e/'source/funkin/backend/system/Main.hx').is_file():
        parser.error('Not a Codename Engine Mobile source tree: '+str(e))
    embed_mod(e)
    patch_project_xml(e)
    patch_main(e)
    print('Prepared APK source. Build with: haxelib run lime build android -final -D ONLY_ARM64')

if __name__=='__main__': main()
