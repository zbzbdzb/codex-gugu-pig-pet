from pathlib import Path
import zipfile,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
selected=['README.md','install.ps1','安装.cmd','preview.html','validation.json','validation-pixels.json','validation-installation.json','TESTING.md','animation.json','sources/manifest.json','previews/all-actions.gif','previews/directions.jpg','previews/cover.png']
selected += [str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'dist').rglob('*') if p.is_file()]
checksums={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in selected}
(ROOT/'SHA256.json').write_text(json.dumps(checksums,ensure_ascii=False,indent=2),encoding='utf-8')
selected.append('SHA256.json')
release=ROOT/'gugu-pig-codex.zip'
with zipfile.ZipFile(release,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in selected: z.write(ROOT/p,'gugu-pig-codex/'+p)
with zipfile.ZipFile(release) as z:
    assert z.testzip() is None
print(json.dumps({'file':str(release),'bytes':release.stat().st_size,'sha256':hashlib.sha256(release.read_bytes()).hexdigest(),'files':len(selected)},indent=2))
